#!/usr/bin/env python3
"""Take screenshots of the admin management features."""

from playwright.sync_api import sync_playwright

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2
        )
        page = context.new_page()

        # Login first
        print("Logging in...")
        page.goto("http://localhost:8080/admin", wait_until="networkidle")
        page.fill('input[type="email"]', 'admin@crosspoint.org')
        page.fill('input[type="password"]', 'cpbcadmin2026')
        page.click('button.submit-button')
        page.wait_for_timeout(3000)

        # Screenshot dashboard with tabs
        print("Taking dashboard with tabs screenshot...")
        page.screenshot(path="/workspaces/cpbc-volunteer-app/admin-tabs.png", full_page=True)

        # Click on Manage Admins tab
        print("Clicking Manage Admins tab...")
        page.click('text=Manage Admins')
        page.wait_for_timeout(2000)

        # Screenshot admin management view
        print("Taking admin management screenshot...")
        page.screenshot(path="/workspaces/cpbc-volunteer-app/admin-management.png", full_page=True)

        # Click Add New Admin button
        print("Opening Add Admin modal...")
        page.click('text=Add New Admin')
        page.wait_for_timeout(500)

        # Screenshot the modal
        print("Taking add admin modal screenshot...")
        page.screenshot(path="/workspaces/cpbc-volunteer-app/admin-add-modal.png")

        # Desktop view
        print("Taking desktop admin management screenshot...")
        page.keyboard.press('Escape')  # Close modal
        page.wait_for_timeout(300)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)
        page.screenshot(path="/workspaces/cpbc-volunteer-app/admin-management-desktop.png", full_page=True)

        browser.close()
        print("Done!")

if __name__ == "__main__":
    take_screenshots()
