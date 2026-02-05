#!/usr/bin/env python3
"""Take screenshots of the admin login and dashboard pages."""

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

        # 1. Screenshot admin login page
        print("Taking admin login screenshot...")
        page.goto("http://localhost:8080/admin", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.screenshot(path="/workspaces/cpbc-volunteer-app/admin-login.png", full_page=True)

        # 2. Login to get dashboard
        print("Logging in...")
        page.fill('input[type="email"]', 'admin@crosspoint.org')
        page.fill('input[type="password"]', 'cpbcadmin2026')
        page.click('button.submit-button')

        # Wait for dashboard to load
        page.wait_for_timeout(3000)

        # 3. Screenshot dashboard
        print("Taking dashboard screenshot...")
        page.screenshot(path="/workspaces/cpbc-volunteer-app/admin-dashboard.png", full_page=True)

        # 4. Take desktop dashboard screenshot
        print("Taking desktop dashboard screenshot...")
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)
        page.screenshot(path="/workspaces/cpbc-volunteer-app/admin-dashboard-desktop.png", full_page=True)

        browser.close()
        print("Done!")

if __name__ == "__main__":
    take_screenshots()
