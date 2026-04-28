# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: meeting-popup.spec.ts >> Meeting Mode Selection Popup >> Accept AI invitation → popup shows → Text Chat works
- Location: tests/meeting-popup.spec.ts:70:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('button:has-text("Accept")').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('button:has-text("Accept")').first()

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - generic [ref=e6]:
        - generic [ref=e7]: P
        - generic [ref=e8]:
          - generic [ref=e9]: Pathfinder
          - generic [ref=e10]: President of Sarmatia · Sarmatia
        - generic [ref=e11]: Head of State
      - generic [ref=e12]:
        - generic [ref=e13]:
          - generic [ref=e14]: R1
          - generic [ref=e15]: H2 2026
        - generic [ref=e16]: OVERTIME
  - navigation [ref=e17]:
    - generic [ref=e18]:
      - generic [ref=e19]:
        - button "Actions" [ref=e20] [cursor=pointer]: Actions
        - button "Confidential" [ref=e22] [cursor=pointer]
        - button "Country" [ref=e23] [cursor=pointer]
        - button "World" [ref=e24] [cursor=pointer]
        - button "Map" [ref=e25] [cursor=pointer]
      - generic [ref=e26]:
        - button "Rules" [ref=e27] [cursor=pointer]
        - button "Navigator" [ref=e28] [cursor=pointer]: Navigator
  - main [ref=e30]:
    - generic [ref=e31]:
      - generic [ref=e32]:
        - heading "Actions Expected Now" [level=3] [ref=e33]
        - paragraph [ref=e34]: No urgent actions at this time.
      - generic [ref=e35]:
        - heading "Active Meetings" [level=3] [ref=e36]
        - generic [ref=e38]:
          - button "WellspringHoS SOLARIA Open Chat" [ref=e39] [cursor=pointer]:
            - generic [ref=e40]: WellspringHoS
            - generic [ref=e41]: SOLARIA
            - generic [ref=e42]: Open Chat
          - button "End meeting" [ref=e43] [cursor=pointer]:
            - img [ref=e44]
      - generic [ref=e46]:
        - heading "General" [level=3] [ref=e47]
        - generic [ref=e48]:
          - button "Public Statement" [ref=e49] [cursor=pointer]
          - button "Set Meetings" [ref=e50] [cursor=pointer]
      - generic [ref=e51]:
        - heading "Economic" [level=3] [ref=e52]
        - generic [ref=e53]:
          - button "Set Budget" [ref=e54] [cursor=pointer]
          - button "Set Tariffs" [ref=e55] [cursor=pointer]
          - button "Set Sanctions" [ref=e56] [cursor=pointer]
          - button "Set Cartel Production" [ref=e57] [cursor=pointer]
      - generic [ref=e58]:
        - heading "International Affairs & Trade" [level=3] [ref=e59]
        - generic [ref=e60]:
          - button "Propose Transaction" [ref=e61] [cursor=pointer]
          - button "Propose Agreement" [ref=e62] [cursor=pointer]
          - button "Grant / Revoke Basing Rights" [ref=e63] [cursor=pointer]
          - button "Declare War" [ref=e64] [cursor=pointer]
      - generic [ref=e65]:
        - heading "Military" [level=3] [ref=e66]
        - generic [ref=e67]:
          - button "Attack" [ref=e68] [cursor=pointer]
          - button "Blockade" [ref=e69] [cursor=pointer]
          - button "Martial Law" [ref=e70] [cursor=pointer]
          - button "Nuclear Test" [ref=e71] [cursor=pointer]
          - button "Nuclear Launch" [ref=e72] [cursor=pointer]
      - generic [ref=e73]:
        - heading "Political" [level=3] [ref=e74]
        - generic [ref=e75]:
          - button "Reassign Powers" [ref=e76] [cursor=pointer]
          - button "Arrest" [ref=e77] [cursor=pointer]
          - button "Change Leader" [ref=e78] [cursor=pointer]
```

# Test source

```ts
  1   | /**
  2   |  * Playwright test: Meeting mode selection popup
  3   |  *
  4   |  * Tests the flow: AI invites human → human accepts → popup shows → select mode → interface opens
  5   |  *
  6   |  * Prerequisites:
  7   |  * - Local frontend running on :5173
  8   |  * - Local backend running on :8000
  9   |  * - FIRST simrun active with AI agents (vizier, wellspring, spire)
  10  |  * - Test user assigned to pathfinder role
  11  |  */
  12  | 
  13  | import { test, expect, type Page } from '@playwright/test'
  14  | import { createClient } from '@supabase/supabase-js'
  15  | 
  16  | const SUPABASE_URL = 'https://lukcymegoldprbovglmn.supabase.co'
  17  | const SUPABASE_ANON_KEY = 'sb_publishable_TR6RrDqyQesOOhWh0qV0gg_kEnLNqc9'
  18  | const FRONTEND_URL = 'http://localhost:5173'
  19  | 
  20  | // Test user credentials — pathfinder's assigned user
  21  | const TEST_EMAIL = 'testbot@metagames.test'
  22  | const TEST_PASSWORD = 'testbot123456'
  23  | 
  24  | const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  25  | 
  26  | // Find the active FIRST simrun
  27  | async function findSimId(): Promise<string> {
  28  |   const { data } = await supabase.from('sim_runs').select('id,name')
  29  |     .in('status', ['active', 'pre_start'])
  30  |     .like('name', '%FIRST%')
  31  |     .limit(1)
  32  |   if (!data?.[0]) throw new Error('No active FIRST simrun found')
  33  |   return data[0].id
  34  | }
  35  | 
  36  | // Create an invitation from AI to human
  37  | async function createInvitation(simId: string, aiRole: string, aiCountry: string, humanRole: string, label: string) {
  38  |   const expires = new Date(Date.now() + 15 * 60000).toISOString()
  39  |   const { data } = await supabase.from('meeting_invitations').insert({
  40  |     sim_run_id: simId,
  41  |     invitation_type: 'one_on_one',
  42  |     inviter_role_id: aiRole,
  43  |     inviter_country_code: aiCountry,
  44  |     invitee_role_id: humanRole,
  45  |     message: `TEST: ${label}`,
  46  |     expires_at: expires,
  47  |     status: 'pending',
  48  |     responses: { _inviter_intent_note: `TEST INTENT: ${label}` },
  49  |   }).select().single()
  50  |   return data
  51  | }
  52  | 
  53  | // Login helper
  54  | async function login(page: Page) {
  55  |   await page.goto(`${FRONTEND_URL}/login`)
  56  |   await page.fill('input[type="email"]', TEST_EMAIL)
  57  |   await page.fill('input[type="password"]', TEST_PASSWORD)
  58  |   await page.click('button[type="submit"]')
  59  |   // Wait for redirect to /play or /dashboard
  60  |   await page.waitForURL(/\/(play|dashboard)/, { timeout: 10000 })
  61  | }
  62  | 
  63  | test.describe('Meeting Mode Selection Popup', () => {
  64  |   let simId: string
  65  | 
  66  |   test.beforeAll(async () => {
  67  |     simId = await findSimId()
  68  |   })
  69  | 
  70  |   test('Accept AI invitation → popup shows → Text Chat works', async ({ page }) => {
  71  |     // Create invitation FIRST (before page load — appears in initial fetch)
  72  |     await createInvitation(simId, 'vizier', 'phrygia', 'pathfinder', 'PW-TextChat-' + Date.now())
  73  | 
  74  |     // Login and navigate
  75  |     await login(page)
  76  |     await page.goto(`${FRONTEND_URL}/play/${simId}`)
  77  |     await page.waitForTimeout(5000)
  78  |     await page.screenshot({ path: 'test-results/01-dashboard-loaded.png' })
  79  | 
  80  |     // Look for the Accept button (invitation should be visible)
  81  |     const acceptBtn = page.locator('button:has-text("Accept")').first()
> 82  |     await expect(acceptBtn).toBeVisible({ timeout: 10000 })
      |                             ^ Error: expect(locator).toBeVisible() failed
  83  |     await page.screenshot({ path: 'test-results/02-invitation-visible.png' })
  84  | 
  85  |     // Click Accept
  86  |     await page.click('button:has-text("Accept")')
  87  | 
  88  |     // Popup should appear
  89  |     const popup = page.locator('text=Connecting you to')
  90  |     await expect(popup).toBeVisible({ timeout: 5000 })
  91  | 
  92  |     // Verify Text Chat button exists
  93  |     const textBtn = page.locator('button:has-text("Text Chat")')
  94  |     await expect(textBtn).toBeVisible()
  95  | 
  96  |     // Click Text Chat
  97  |     await textBtn.click()
  98  | 
  99  |     // MeetingChat should appear
  100 |     await expect(page.locator('text=Type a message')).toBeVisible({ timeout: 5000 })
  101 |   })
  102 | 
  103 |   test('Accept AI invitation → popup shows → Voice Call button visible when AI has voice', async ({ page }) => {
  104 |     await login(page)
  105 |     await page.goto(`${FRONTEND_URL}/play/${simId}`)
  106 |     await page.waitForSelector('.font-heading', { timeout: 10000 })
  107 |     await page.waitForTimeout(2000)
  108 | 
  109 |     const inv = await createInvitation(simId, 'wellspring', 'solaria', 'pathfinder', 'Playwright Voice Test')
  110 | 
  111 |     await page.waitForSelector('text=Playwright Voice Test', { timeout: 10000 })
  112 |     await page.click('button:has-text("Accept")')
  113 | 
  114 |     const popup = page.locator('text=Connecting you to')
  115 |     await expect(popup).toBeVisible({ timeout: 5000 })
  116 | 
  117 |     // Both buttons should be visible
  118 |     await expect(page.locator('button:has-text("Text Chat")')).toBeVisible()
  119 |     await expect(page.locator('button:has-text("Voice Call")')).toBeVisible()
  120 | 
  121 |     // Click Text Chat (voice requires ElevenLabs which we can't automate)
  122 |     await page.click('button:has-text("Text Chat")')
  123 |     await expect(page.locator('text=Type a message')).toBeVisible({ timeout: 5000 })
  124 |   })
  125 | 
  126 |   test('Reject invitation → no popup, no meeting', async ({ page }) => {
  127 |     await login(page)
  128 |     await page.goto(`${FRONTEND_URL}/play/${simId}`)
  129 |     await page.waitForSelector('.font-heading', { timeout: 10000 })
  130 |     await page.waitForTimeout(2000)
  131 | 
  132 |     await createInvitation(simId, 'spire', 'mirage', 'pathfinder', 'Playwright Reject Test')
  133 | 
  134 |     await page.waitForSelector('text=Playwright Reject Test', { timeout: 10000 })
  135 |     await page.click('button:has-text("Decline")')
  136 | 
  137 |     // No popup should appear
  138 |     await page.waitForTimeout(2000)
  139 |     await expect(page.locator('text=Connecting you to')).not.toBeVisible()
  140 |   })
  141 | 
  142 |   test('Popup buttons respond within 1 second', async ({ page }) => {
  143 |     await login(page)
  144 |     await page.goto(`${FRONTEND_URL}/play/${simId}`)
  145 |     await page.waitForSelector('.font-heading', { timeout: 10000 })
  146 |     await page.waitForTimeout(3000) // Extra wait for allRoleInfo
  147 | 
  148 |     await createInvitation(simId, 'vizier', 'phrygia', 'pathfinder', 'Playwright Speed Test')
  149 | 
  150 |     await page.waitForSelector('text=Playwright Speed Test', { timeout: 10000 })
  151 |     await page.click('button:has-text("Accept")')
  152 | 
  153 |     await expect(page.locator('text=Connecting you to')).toBeVisible({ timeout: 5000 })
  154 | 
  155 |     // Time the button click
  156 |     const start = Date.now()
  157 |     await page.click('button:has-text("Text Chat")')
  158 |     const elapsed = Date.now() - start
  159 | 
  160 |     // Should respond in under 1 second
  161 |     expect(elapsed).toBeLessThan(1000)
  162 | 
  163 |     // Chat should appear
  164 |     await expect(page.locator('text=Type a message')).toBeVisible({ timeout: 5000 })
  165 |   })
  166 | })
  167 | 
```