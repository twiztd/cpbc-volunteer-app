#!/usr/bin/env python3
"""Take screenshots of the edit volunteer modal."""

from playwright.sync_api import sync_playwright

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Mobile viewport
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

        # Click on a volunteer to open edit modal
        print("Opening edit volunteer modal...")
        page.click('.volunteer-card.clickable')
        page.wait_for_timeout(1500)

        # Screenshot the modal
        print("Taking mobile modal screenshot...")
        page.screenshot(path="/workspaces/cpbc-volunteer-app/edit-modal-mobile.png")

        # Scroll down in the modal to see notes section
        print("Scrolling to notes section...")
        modal_body = page.locator('.modal-body')
        modal_body.evaluate('el => el.scrollTop = el.scrollHeight')
        page.wait_for_timeout(500)
        page.screenshot(path="/workspaces/cpbc-volunteer-app/edit-modal-mobile-notes.png")

        # Desktop viewport
        print("Taking desktop modal screenshot...")
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)
        modal_body.evaluate('el => el.scrollTop = 0')
        page.wait_for_timeout(300)
        page.screenshot(path="/workspaces/cpbc-volunteer-app/edit-modal-desktop.png")

        browser.close()
        print("Done!")

if __name__ == "__main__":
    take_screenshots()
