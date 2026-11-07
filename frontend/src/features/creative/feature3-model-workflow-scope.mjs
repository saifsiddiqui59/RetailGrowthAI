/** Ephemeral browser-only reviewer state scope: never a JWT or server grant. */
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const sessions=new WeakMap()
let next=0
export function feature3ModelWorkflowSessionKey(shopId,api) {
 if(typeof shopId!=='string'||!UUID.test(shopId)||!api||
    (typeof api!=='object'&&typeof api!=='function'))return null
 let number=sessions.get(api)
 if(!number){number=++next;sessions.set(api,number)}
 return shopId.toLowerCase()+':'+number
}
