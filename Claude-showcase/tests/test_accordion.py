import os
import sys
import time
import subprocess
import signal
from playwright.sync_api import sync_playwright

def test_accordion():
    # Start the local server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give the server a moment to start
    time.sleep(2)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Disable external resources to speed up loading
        context = browser.new_context()
        page = context.new_page()

        page.route("**/*.{png,jpg,jpeg,svg,woff,woff2,ttf}", lambda route: route.abort())
        page.route("**/fonts.googleapis.com/**", lambda route: route.abort())
        page.route("**/fonts.gstatic.com/**", lambda route: route.abort())

        url = "http://localhost:8001/Claude-showcase/index.html"

        print(f"Navigating to {url}...")
        try:
            page.goto(url, timeout=60000, wait_until="load")
        except Exception as e:
            print(f"Navigation warning: {e}")

        # Wait for accordion container to be present
        try:
            page.wait_for_selector("#accordion", timeout=20000)
            print("Found #accordion container.")
        except Exception as e:
            print("Timeout waiting for #accordion container")
            browser.close()
            server_process.terminate()
            sys.exit(1)

        # Wait for items to be populated
        page.wait_for_function("document.querySelectorAll('.accordion-item').length > 0")

        items = page.locator(".accordion-item")
        count = items.count()
        print(f"Found {count} accordion items.")

        if count == 0:
            print("Error: No accordion items found.")
            browser.close()
            server_process.terminate()
            sys.exit(1)

        # 1. Initially, no item should be open
        for i in range(count):
            classes = items.nth(i).get_attribute("class")
            if classes and "open" in classes:
                print(f"Error: Item {i} is initially open.")
                browser.close()
                server_process.terminate()
                sys.exit(1)

        # 2. Click the first item - should open
        print("Testing click on first item...")
        items.nth(0).locator(".accordion-trigger").click()

        # Instead of time.sleep, wait for the class to change
        try:
            page.wait_for_function(
                "idx => document.querySelectorAll('.accordion-item')[idx].classList.contains('open')",
                arg=0,
                timeout=5000
            )
        except Exception:
            print("Error: First item did not open after click.")
            browser.close()
            server_process.terminate()
            sys.exit(1)

        # 3. Click the second item - it should open and the first one should close
        if count > 1:
            print("Testing click on second item...")
            items.nth(1).locator(".accordion-trigger").click()

            try:
                page.wait_for_function(
                    "idx => document.querySelectorAll('.accordion-item')[idx].classList.contains('open')",
                    arg=1,
                    timeout=5000
                )
                page.wait_for_function(
                    "idx => !document.querySelectorAll('.accordion-item')[idx].classList.contains('open')",
                    arg=0,
                    timeout=5000
                )
            except Exception:
                print("Error: Accordion behavior incorrect after clicking second item.")
                browser.close()
                server_process.terminate()
                sys.exit(1)

            # 4. Click the second item again - it should close (toggle)
            print("Testing toggle off second item...")
            items.nth(1).locator(".accordion-trigger").click()

            try:
                page.wait_for_function(
                    "idx => !document.querySelectorAll('.accordion-item')[idx].classList.contains('open')",
                    arg=1,
                    timeout=5000
                )
            except Exception:
                print("Error: Second item did not close after second click.")
                browser.close()
                server_process.terminate()
                sys.exit(1)

        print("All accordion tests passed successfully!")
        browser.close()
        server_process.terminate()

if __name__ == "__main__":
    test_accordion()
