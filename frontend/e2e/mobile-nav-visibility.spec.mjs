import { test, expect } from '@playwright/test'

const HOST='https://e2e.supabase.test'
const SHOP='a1000000-0000-4000-8000-000000000001'
const USER='a9000000-0000-4000-8000-000000000001'

async function signInOffline(page) {
  await page.route(HOST+'/**',route=>{
    const path=new URL(route.request().url()).pathname
    const values={
      '/auth/v1/user':{id:USER,email:'owner@example.test'},
      '/rest/v1/rpc/retail_platform_me':false,
      '/rest/v1/shop_memberships':[{shop_id:SHOP,role:'OWNER',active:true}],
      '/rest/v1/shops':[{id:SHOP,name:'Boutique',slug:'boutique'}],
      '/rest/v1/media_assets':[],
    }
    if(route.request().method()==='OPTIONS') return route.fulfill({
      status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},body:''
    })
    if(route.request().method()==='HEAD') return route.fulfill({
      status:200,headers:{'Access-Control-Allow-Origin':'*','Content-Range':'*/0'},body:''
    })
    if(!(path in values)) throw Error('Unexpected offline endpoint '+path)
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify(values[path])})
  })
  await page.addInitScript(()=>sessionStorage.setItem('retailgrowthai-auth-v1',
    JSON.stringify({access_token:'offline-test-JWT',refresh_token:'offline-refresh',
      expires_at:2000000000})))
}
test('closed mobile navigation is hidden from keyboard and screen-reader tree',async({page})=>{
  await page.setViewportSize({width:320,height:740})
  await signInOffline(page)
  await page.goto('/')
  const sidebar=page.locator('.retail-shell .sidebar')
  const toggle=page.getByRole('button',{name:'Toggle navigation'})
  await expect(page.getByRole('heading',{name:'Campaign workspace'})).toBeVisible()
  await expect(toggle).toHaveAttribute('aria-expanded','false')
  await expect(sidebar).toHaveCSS('visibility','hidden')
  await expect(page.getByRole('navigation',{name:'Main navigation'})).toHaveCount(0)
  await toggle.click()
  await expect(toggle).toHaveAttribute('aria-expanded','true')
  await expect(sidebar).toBeVisible()
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Media library'}).click()
  await expect(page.getByRole('heading',{name:'Media library'})).toBeVisible()
  await expect(sidebar).toHaveCSS('visibility','hidden')
  await expect(page.getByRole('navigation',{name:'Main navigation'})).toHaveCount(0)
  await toggle.click()
  await expect(sidebar).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(toggle).toHaveAttribute('aria-expanded','false')
  await expect(sidebar).toHaveCSS('visibility','hidden')
})
test('desktop workspace navigation remains visible and usable',async({page})=>{
  await page.setViewportSize({width:1280,height:850})
  await signInOffline(page)
  await page.goto('/')
  await expect(page.getByRole('heading',{name:'Campaign workspace'})).toBeVisible()
  await expect(page.getByRole('navigation',{name:'Main navigation'})).toBeVisible()
  await expect(page.locator('.retail-shell .sidebar')).toHaveCSS('visibility','visible')
})
