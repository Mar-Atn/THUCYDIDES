# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: meeting-popup.spec.ts >> Meeting Mode Selection Popup >> Popup buttons respond within 2 seconds
- Location: tests/meeting-popup.spec.ts:144:3

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
        - generic [ref=e37]:
          - generic [ref=e38]:
            - button "WellspringHoS SOLARIA Open Chat" [ref=e39] [cursor=pointer]:
              - generic [ref=e40]: WellspringHoS
              - generic [ref=e41]: SOLARIA
              - generic [ref=e42]: Open Chat
            - button "End meeting" [ref=e43] [cursor=pointer]:
              - img [ref=e44]
          - generic [ref=e46]:
            - button "VizierHoS PHRYGIA Open Chat" [ref=e47] [cursor=pointer]:
              - generic [ref=e48]: VizierHoS
              - generic [ref=e49]: PHRYGIA
              - generic [ref=e50]: Open Chat
            - button "End meeting" [ref=e51] [cursor=pointer]:
              - img [ref=e52]
          - generic [ref=e54]:
            - button "WellspringHoS SOLARIA Open Chat" [ref=e55] [cursor=pointer]:
              - generic [ref=e56]: WellspringHoS
              - generic [ref=e57]: SOLARIA
              - generic [ref=e58]: Open Chat
            - button "End meeting" [ref=e59] [cursor=pointer]:
              - img [ref=e60]
          - generic [ref=e62]:
            - button "VizierHoS PHRYGIA Open Chat" [ref=e63] [cursor=pointer]:
              - generic [ref=e64]: VizierHoS
              - generic [ref=e65]: PHRYGIA
              - generic [ref=e66]: Open Chat
            - button "End meeting" [ref=e67] [cursor=pointer]:
              - img [ref=e68]
          - generic [ref=e70]:
            - button "SpireHoS MIRAGE Open Chat" [ref=e71] [cursor=pointer]:
              - generic [ref=e72]: SpireHoS
              - generic [ref=e73]: MIRAGE
              - generic [ref=e74]: Open Chat
            - button "End meeting" [ref=e75] [cursor=pointer]:
              - img [ref=e76]
      - generic [ref=e78]:
        - heading "General" [level=3] [ref=e79]
        - generic [ref=e80]:
          - button "Public Statement" [ref=e81] [cursor=pointer]
          - button "Set Meetings" [ref=e82] [cursor=pointer]
      - generic [ref=e83]:
        - heading "Economic" [level=3] [ref=e84]
        - generic [ref=e85]:
          - button "Set Budget" [ref=e86] [cursor=pointer]
          - button "Set Tariffs" [ref=e87] [cursor=pointer]
          - button "Set Sanctions" [ref=e88] [cursor=pointer]
          - button "Set Cartel Production" [ref=e89] [cursor=pointer]
      - generic [ref=e90]:
        - heading "International Affairs & Trade" [level=3] [ref=e91]
        - generic [ref=e92]:
          - button "Propose Transaction" [ref=e93] [cursor=pointer]
          - button "Propose Agreement" [ref=e94] [cursor=pointer]
          - button "Grant / Revoke Basing Rights" [ref=e95] [cursor=pointer]
          - button "Declare War" [ref=e96] [cursor=pointer]
      - generic [ref=e97]:
        - heading "Military" [level=3] [ref=e98]
        - generic [ref=e99]:
          - button "Attack" [ref=e100] [cursor=pointer]
          - button "Blockade" [ref=e101] [cursor=pointer]
          - button "Martial Law" [ref=e102] [cursor=pointer]
          - button "Nuclear Test" [ref=e103] [cursor=pointer]
          - button "Nuclear Launch" [ref=e104] [cursor=pointer]
      - generic [ref=e105]:
        - heading "Political" [level=3] [ref=e106]
        - generic [ref=e107]:
          - button "Reassign Powers" [ref=e108] [cursor=pointer]
          - button "Arrest" [ref=e109] [cursor=pointer]
          - button "Change Leader" [ref=e110] [cursor=pointer]
```

# Test source

```ts
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
  82  |     await expect(acceptBtn).toBeVisible({ timeout: 10000 })
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
  99  |     // MeetingChat should appear (check for input placeholder)
  100 |     await page.screenshot({ path: 'test-results/03-after-text-chat-click.png' })
  101 |     await expect(page.locator('textarea[placeholder="Type a message..."]')).toBeVisible({ timeout: 10000 })
  102 |   })
  103 | 
  104 |   test('Accept AI invitation → popup shows → Voice Call button visible when AI has voice', async ({ page }) => {
  105 |     // Create invitation before page load
  106 |     await createInvitation(simId, 'wellspring', 'solaria', 'pathfinder', 'PW-Voice-' + Date.now())
  107 | 
  108 |     await login(page)
  109 |     await page.goto(`${FRONTEND_URL}/play/${simId}`)
  110 |     await page.waitForTimeout(5000)
  111 | 
  112 |     const acceptBtn = page.locator('button:has-text("Accept")').first()
  113 |     await expect(acceptBtn).toBeVisible({ timeout: 10000 })
  114 |     await acceptBtn.click()
  115 | 
  116 |     const popup = page.locator('text=Connecting you to')
  117 |     await expect(popup).toBeVisible({ timeout: 5000 })
  118 | 
  119 |     // Both buttons should be visible (AI has voice agent)
  120 |     await expect(page.locator('button:has-text("Text Chat")')).toBeVisible()
  121 |     await expect(page.locator('button:has-text("Voice Call")')).toBeVisible()
  122 | 
  123 |     // Click Text Chat (voice requires ElevenLabs — can't automate)
  124 |     await page.click('button:has-text("Text Chat")')
  125 |     await expect(page.locator('textarea[placeholder="Type a message..."]')).toBeVisible({ timeout: 10000 })
  126 |   })
  127 | 
  128 |   test('Reject invitation → no popup, no meeting', async ({ page }) => {
  129 |     await createInvitation(simId, 'spire', 'mirage', 'pathfinder', 'PW-Reject-' + Date.now())
  130 | 
  131 |     await login(page)
  132 |     await page.goto(`${FRONTEND_URL}/play/${simId}`)
  133 |     await page.waitForTimeout(5000)
  134 | 
  135 |     const declineBtn = page.locator('button:has-text("Decline")').first()
  136 |     await expect(declineBtn).toBeVisible({ timeout: 10000 })
  137 |     await declineBtn.click()
  138 | 
  139 |     // No popup should appear
  140 |     await page.waitForTimeout(2000)
  141 |     await expect(page.locator('text=Connecting you to')).not.toBeVisible()
  142 |   })
  143 | 
  144 |   test('Popup buttons respond within 2 seconds', async ({ page }) => {
  145 |     await createInvitation(simId, 'vizier', 'phrygia', 'pathfinder', 'PW-Speed-' + Date.now())
  146 | 
  147 |     await login(page)
  148 |     await page.goto(`${FRONTEND_URL}/play/${simId}`)
  149 |     await page.waitForTimeout(5000)
  150 | 
  151 |     const acceptBtn = page.locator('button:has-text("Accept")').first()
> 152 |     await expect(acceptBtn).toBeVisible({ timeout: 10000 })
      |                             ^ Error: expect(locator).toBeVisible() failed
  153 |     await acceptBtn.click()
  154 | 
  155 |     await expect(page.locator('text=Connecting you to')).toBeVisible({ timeout: 5000 })
  156 | 
  157 |     // Time the button click
  158 |     const start = Date.now()
  159 |     await page.click('button:has-text("Text Chat")')
  160 |     const elapsed = Date.now() - start
  161 | 
  162 |     // Should respond within 2 seconds (was hanging indefinitely before)
  163 |     expect(elapsed).toBeLessThan(2000)
  164 | 
  165 |     await expect(page.locator('textarea[placeholder="Type a message..."]')).toBeVisible({ timeout: 10000 })
  166 |   })
  167 | })
  168 | 
```