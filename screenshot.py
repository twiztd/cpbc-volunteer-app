#!/usr/bin/env python3
"""Take screenshots of the volunteer form at mobile viewport size."""

from playwright.sync_api import sync_playwright

def take_screenshots():
    with sync_playwright() as p:
        # Launch headless Chromium
        browser = p.chromium.launch(headless=True)

        # Create context with iPhone 14 viewport size
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2
        )

        page = context.new_page()

        # Navigate to the app
        print("Navigating to http://localhost:8080/...")
        page.goto("http://localhost:8080/", wait_until="networkidle")

        # Wait for content to load
        page.wait_for_timeout(2000)

        # Take full-page screenshot from top
        print("Taking top screenshot...")
        page.screenshot(path="/workspaces/cpbc-volunteer-app/mobile-form.png", full_page=True)

        # Scroll to bottom
        print("Scrolling to bottom...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)

        # Take screenshot of bottom portion (viewport only, not full page)
        print("Taking bottom screenshot...")
        page.screenshot(path="/workspaces/cpbc-volunteer-app/mobile-form-bottom.png")

        browser.close()
        print("Done!")

if __name__ == "__main__":
    take_screenshots()
