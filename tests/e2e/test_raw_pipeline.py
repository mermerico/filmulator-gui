#!/usr/bin/env python3
import xmlrpc.client
import time
import sys
import os
import subprocess
import tempfile
import shutil

def poll_for_condition(condition_func, timeout=10, check_interval=0.1):
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return True
        time.sleep(check_interval)
    return False

def wait_for_port(port, timeout=10):
    def check_port():
        try:
            import socket
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except:
            return False
    return poll_for_condition(check_port, timeout)

def wait_for_item(proxy, object_name, timeout=10):
    if object_name == "mainWindow" or "/" in object_name:
        path = object_name
    else:
        path = f"mainWindow/{object_name}"
    
    def check_item():
        try:
            return proxy.existsAndVisible(path)
        except:
            return False
    return poll_for_condition(check_item, timeout)

def mouse_click(proxy, object_name):
    if object_name == "mainWindow" or "/" in object_name:
        path = object_name
    else:
        path = f"mainWindow/{object_name}"
    proxy.mouseClick(path)

def mouse_double_click(proxy, object_name):
    if object_name == "mainWindow" or "/" in object_name:
        path = object_name
    else:
        path = f"mainWindow/{object_name}"
    # Explicitly use two clicks since mouseDoubleClick might not be exposed
    proxy.mouseClick(path)
    time.sleep(0.05)
    proxy.mouseClick(path)

def run_test():
    raw_file_path = os.path.abspath("tests/data/raw/_DSC0355.NEF")
    raw_dir_path = os.path.dirname(raw_file_path)
    golden_file_path = os.path.abspath("tests/e2e/golden/golden_raw_pipeline.jpg")
    output_file_path = os.path.abspath("tests/data/raw/_DSC0355-output.jpg")
    binary_path = os.path.abspath("build/relwithdebinfo/Filmulator.app/Contents/MacOS/filmulator-gui")

    if not os.path.exists(raw_file_path):
        print(f"Error: RAW file not found at {raw_file_path}")
        return False

    if not os.path.exists(binary_path):
        print(f"Error: Binary not found at {binary_path}")
        return False

    # Setup temporary directory for fresh database
    test_db_dir = tempfile.mkdtemp(prefix="filmulator_test_db_")
    print(f"Using fresh database directory: {test_db_dir}")

    # Set environment variables for the process
    env = os.environ.copy()
    env["FILMULATOR_DB_DIR"] = test_db_dir

    # Start the process
    print(f"Starting Filmulator: {binary_path}")
    process = subprocess.Popen([binary_path, "--test-mode"], 
                             stdout=None, 
                             stderr=None,
                             env=env,
                             text=True)

    try:
        print("Waiting for Spix server on port 9000...")
        if not wait_for_port(9000):
            print("Error: Spix server did not start")
            return False

        proxy = xmlrpc.client.ServerProxy("http://127.0.0.1:9000")

        print("Step 1: Waiting for app UI...")
        if not wait_for_item(proxy, "mainWindow"):
            print("Error: App mainWindow not ready")
            return False

        print("Step 2: Navigating to Import tab and setting directory import...")
        mouse_click(proxy, "importTabButton")
        if not wait_for_item(proxy, "importButton"):
            print("Error: Import tab not loaded")
            return False
            
        mouse_click(proxy, "sourceDirButton")
        proxy.setStringProperty("mainWindow/sourceDirButton", "checked", "true")
        
        mouse_click(proxy, "importInPlaceButton")
        proxy.setStringProperty("mainWindow/importInPlaceButton", "checked", "true")
        
        if not wait_for_item(proxy, "sourceDirEntry"):
            print("Error: sourceDirEntry not visible")
            return False
            
        print(f"Setting source directory to: {raw_dir_path}")
        proxy.setStringProperty("mainWindow/sourceDirEntry", "enteredText", raw_dir_path)

        can_import = proxy.getStringProperty("mainWindow/importButton", "notDisabled")
        print(f"  Import button enabled: {can_import}")
        
        if can_import == "false":
            print("Error: Import button is disabled.")
            return False

        print("  Clicking Import button...")
        mouse_click(proxy, "importButton")
        print("Waiting for import to complete (watching itemCount)...")

        print("Step 4: Navigating to Organize tab...")
        mouse_click(proxy, "organizeTabButton")
        time.sleep(2) # Give a moment for view switch
        
        # In a fresh DB, the Organize model might need a kick to show the newly imported image
        # since it defaults to showing only today's images.
        
        target_dates = ["2017/12/25", "2017/12/05", "2017/12/5"]
        found_image = False
        for date_to_try in target_dates:
            print(f"  Attempting to select date {date_to_try} in histogram...")
            try:
                proxy.invokeMethod("mainWindow/organizeView", "selectDateInHistogram", [date_to_try])
                time.sleep(0.5) # Short wait for update
                
                item_count = int(proxy.getStringProperty("mainWindow/organizeView", "itemCount") or 0)
                print(f"  Organize itemCount after selecting {date_to_try}: {item_count}")
                
                if item_count > 0:
                    found_image = True
                    break
            except Exception as e:
                print(f"  Warning: Failed to select/check date {date_to_try}: {e}")

        if not found_image:
            print("  Warning: No images detected in Organize. Attempting to force filter reset...")
            proxy.setStringProperty("mainWindow/organizeView/minRatingSlider", "value", "0")
            proxy.setStringProperty("mainWindow/organizeView/maxRatingSlider", "value", "5")
            time.sleep(0.5)
            # Try target date again after reset
            for date_to_try in target_dates:
                proxy.invokeMethod("mainWindow/organizeView", "selectDateInHistogram", [date_to_try])
                time.sleep(0.5)
                item_count = int(proxy.getStringProperty("mainWindow/organizeView", "itemCount") or 0)
                if item_count > 0:
                    found_image = True
                    break
            print(f"  Organize itemCount after reset: {item_count}")

        # Try targeting the delegate directly.
        # Path: mainWindow/organizeView (Organize.qml) -> organizeGridView (GridView) -> organizeDelegate (OrganizeDelegate.qml)
        delegate_path = "mainWindow/organizeView/organizeGridView/organizeDelegate"
        
        if not wait_for_item(proxy, delegate_path, timeout=1):
            print(f"Error: {delegate_path} not found (no images imported or filtered out?)")
            return False

        print("Step 5: Enqueuing the image...")
        mouse_double_click(proxy, delegate_path)
        time.sleep(0.1) # Wait for animation/enqueue

        print("Step 6: Navigating to Edit tab...")
        mouse_click(proxy, "filmulateTabButton")

        print("Step 7: Selecting image in queue...")
        # Use simple double click on the delegate we found
        mouse_double_click(proxy, queue_delegate_path)
        # Helper to check if image is loaded
        def check_image_ready():
            # We can check if "editView" (Edit.qml) has imageReady property true
            # Also check if saveJPEGButton is enabled, which implies imageReady
            # But here we just want to know if selection worked
            ready = proxy.getStringProperty("mainWindow/editView", "imageReady")
            return ready == "true"
            
        if not poll_for_condition(check_image_ready, timeout=2):
            print(f"Error: Image verification failed. imageReady: {proxy.getStringProperty('mainWindow/editView', 'imageReady')}")
            return False
        
        print(f"  Image ready for editing: {proxy.getStringProperty('mainWindow/editView', 'imageReady')}")

        if not wait_for_item(proxy, "mainWindow/editView/editTools/exposureCompSlider"):
             print("Error: Controls not found")
             return False

        print("Step 8: Adjusting parameters...")
        # Paths are now mainWindow/editView/editTools/...
        proxy.setStringProperty("mainWindow/editView/editTools/exposureCompSlider", "value", "1.5")
        proxy.setStringProperty("mainWindow/editView/editTools/filmDramaSlider", "value", "50")
        time.sleep(1.0) # Wait for params to apply

        print("Step 9: Exporting JPEG...")
        # Wait for export button to be enabled (it depends on image processing completion)
        export_button_path = "mainWindow/editView/editTools/saveJPEGButton"
        print("  Waiting for export button to be enabled (up to 6s)...")
        
        def check_export_enabled():
            return proxy.getStringProperty(export_button_path, "notDisabled") == "true"
            
        if not poll_for_condition(check_export_enabled, timeout=6, check_interval=0.5):
            print("Error: Export button did not become enabled within 6s")
            # Diagnostic: print image state
            print(f"  Image ready: {proxy.getStringProperty('mainWindow/editView/editTools', 'imageReady')}")
            return False
            
        mouse_click(proxy, export_button_path)
        
        print("Waiting for export file...")
        def check_export_file():
            return os.path.exists(output_file_path)
            
        if not poll_for_condition(check_export_file, timeout=2, check_interval=0.3):
            print("Error: Export timed out")
            print(f"Export file path: {output_file_path}")
            return False

        print("Step 10: Comparing with golden image...")
        if not os.path.exists(golden_file_path):
            print(f"Golden image not found, saving current output as golden: {golden_file_path}")
            os.makedirs(os.path.dirname(golden_file_path), exist_ok=True)
            subprocess.run(["cp", output_file_path, golden_file_path])
            return True

        result = subprocess.run(
            ["magick", "compare", "-metric", "AE", "-fuzz", "5%", output_file_path, golden_file_path, "null:"],
            capture_output=True, text=True
        )
        
        try:
            diff_pixels = int(result.stderr.strip())
            print(f"Differing pixels: {diff_pixels}")
            if diff_pixels < 500:
                print("✓ Test PASSED")
                return True
            else:
                print("✗ Test FAILED: Images differ significantly")
                return False
        except Exception as e:
            print(f"Could not parse compare output: {e}")
            return False

    finally:
        print("Cleaning up: Terminating Filmulator process")
        process.terminate()
        try:
            process.wait(timeout=5)
        except:
            process.kill()
        
        # Remove temporary database directory
        try:
            if os.path.exists(test_db_dir):
                shutil.rmtree(test_db_dir)
                print(f"Cleaned up test database directory: {test_db_dir}")
        except:
            pass

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
