/**
 * Playwright test: Meeting mode selection popup
 *
 * Tests the flow: AI invites human → human accepts → popup shows → select mode → interface opens
 *
 * Prerequisites:
 * - Local frontend running on :5173
 * - Local backend running on :8000
 * - FIRST simrun active with AI agents (vizier, wellspring, spire)
 * - Test user assigned to pathfinder role
 */

import { test, expect, type Page } from '@playwright/test'
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://lukcymegoldprbovglmn.supabase.co'
const SUPABASE_ANON_KEY = 'sb_publishable_TR6RrDqyQesOOhWh0qV0gg_kEnLNqc9'
const FRONTEND_URL = 'http://localhost:5173'

// Test user credentials — pathfinder's assigned user
const TEST_EMAIL = 'testbot@metagames.test'
const TEST_PASSWORD = 'testbot123456'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Find the active FIRST simrun
async function findSimId(): Promise<string> {
  const { data } = await supabase.from('sim_runs').select('id,name')
    .in('status', ['active', 'pre_start'])
    .like('name', '%FIRST%')
    .limit(1)
  if (!data?.[0]) throw new Error('No active FIRST simrun found')
  return data[0].id
}

// Create an invitation from AI to human
async function createInvitation(simId: string, aiRole: string, aiCountry: string, humanRole: string, label: string) {
  const expires = new Date(Date.now() + 15 * 60000).toISOString()
  const { data } = await supabase.from('meeting_invitations').insert({
    sim_run_id: simId,
    invitation_type: 'one_on_one',
    inviter_role_id: aiRole,
    inviter_country_code: aiCountry,
    invitee_role_id: humanRole,
    message: `TEST: ${label}`,
    expires_at: expires,
    status: 'pending',
    responses: { _inviter_intent_note: `TEST INTENT: ${label}` },
  }).select().single()
  return data
}

// Login helper
async function login(page: Page) {
  await page.goto(`${FRONTEND_URL}/login`)
  await page.fill('input[type="email"]', TEST_EMAIL)
  await page.fill('input[type="password"]', TEST_PASSWORD)
  await page.click('button[type="submit"]')
  // Wait for redirect to /play or /dashboard
  await page.waitForURL(/\/(play|dashboard)/, { timeout: 10000 })
}

test.describe('Meeting Mode Selection Popup', () => {
  let simId: string

  test.beforeAll(async () => {
    simId = await findSimId()
  })

  test('Accept AI invitation → popup shows → Text Chat works', async ({ page }) => {
    // Create invitation FIRST (before page load — appears in initial fetch)
    await createInvitation(simId, 'vizier', 'phrygia', 'pathfinder', 'PW-TextChat-' + Date.now())

    // Login and navigate
    await login(page)
    await page.goto(`${FRONTEND_URL}/play/${simId}`)
    await page.waitForTimeout(5000)
    await page.screenshot({ path: 'test-results/01-dashboard-loaded.png' })

    // Look for the Accept button (invitation should be visible)
    const acceptBtn = page.locator('button:has-text("Accept")').first()
    await expect(acceptBtn).toBeVisible({ timeout: 10000 })
    await page.screenshot({ path: 'test-results/02-invitation-visible.png' })

    // Click Accept
    await page.click('button:has-text("Accept")')

    // Popup should appear
    const popup = page.locator('text=Connecting you to')
    await expect(popup).toBeVisible({ timeout: 5000 })

    // Verify Text Chat button exists
    const textBtn = page.locator('button:has-text("Text Chat")')
    await expect(textBtn).toBeVisible()

    // Click Text Chat
    await textBtn.click()

    // MeetingChat should appear
    await expect(page.locator('text=Type a message')).toBeVisible({ timeout: 5000 })
  })

  test('Accept AI invitation → popup shows → Voice Call button visible when AI has voice', async ({ page }) => {
    await login(page)
    await page.goto(`${FRONTEND_URL}/play/${simId}`)
    await page.waitForSelector('.font-heading', { timeout: 10000 })
    await page.waitForTimeout(2000)

    const inv = await createInvitation(simId, 'wellspring', 'solaria', 'pathfinder', 'Playwright Voice Test')

    await page.waitForSelector('text=Playwright Voice Test', { timeout: 10000 })
    await page.click('button:has-text("Accept")')

    const popup = page.locator('text=Connecting you to')
    await expect(popup).toBeVisible({ timeout: 5000 })

    // Both buttons should be visible
    await expect(page.locator('button:has-text("Text Chat")')).toBeVisible()
    await expect(page.locator('button:has-text("Voice Call")')).toBeVisible()

    // Click Text Chat (voice requires ElevenLabs which we can't automate)
    await page.click('button:has-text("Text Chat")')
    await expect(page.locator('text=Type a message')).toBeVisible({ timeout: 5000 })
  })

  test('Reject invitation → no popup, no meeting', async ({ page }) => {
    await login(page)
    await page.goto(`${FRONTEND_URL}/play/${simId}`)
    await page.waitForSelector('.font-heading', { timeout: 10000 })
    await page.waitForTimeout(2000)

    await createInvitation(simId, 'spire', 'mirage', 'pathfinder', 'Playwright Reject Test')

    await page.waitForSelector('text=Playwright Reject Test', { timeout: 10000 })
    await page.click('button:has-text("Decline")')

    // No popup should appear
    await page.waitForTimeout(2000)
    await expect(page.locator('text=Connecting you to')).not.toBeVisible()
  })

  test('Popup buttons respond within 1 second', async ({ page }) => {
    await login(page)
    await page.goto(`${FRONTEND_URL}/play/${simId}`)
    await page.waitForSelector('.font-heading', { timeout: 10000 })
    await page.waitForTimeout(3000) // Extra wait for allRoleInfo

    await createInvitation(simId, 'vizier', 'phrygia', 'pathfinder', 'Playwright Speed Test')

    await page.waitForSelector('text=Playwright Speed Test', { timeout: 10000 })
    await page.click('button:has-text("Accept")')

    await expect(page.locator('text=Connecting you to')).toBeVisible({ timeout: 5000 })

    // Time the button click
    const start = Date.now()
    await page.click('button:has-text("Text Chat")')
    const elapsed = Date.now() - start

    // Should respond in under 1 second
    expect(elapsed).toBeLessThan(1000)

    // Chat should appear
    await expect(page.locator('text=Type a message')).toBeVisible({ timeout: 5000 })
  })
})
