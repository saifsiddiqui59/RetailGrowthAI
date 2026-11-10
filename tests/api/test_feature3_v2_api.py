"""Offline Feature3 v2 API: no JWT bypass, other-shop media or stored render."""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'azure-functions' / 'campaign-api'))
from feature3_v2_api import Feature3V2API
from feature3_v2_store import Feature3V2Store
from tenant_store import StorageUnavailable

class FakeTenant:
    def __init__(self, sid, cid, did):
        self.sid,self.cid,self.did = sid,cid,did
        self.role = 'OWNER'
        self.day_status = 'DRAFT'
        self.campaign_status = 'DRAFT'
    def member(self, token, uid, sid, write=False):
        return token=='signed-owner-jwt' and sid==self.sid and self.role in (
            ('OWNER','EDITOR') if write else ('OWNER','EDITOR','VIEWER'))
    def campaign(self, token, uid, cid):
        if cid!=self.cid or not self.member(token,uid,self.sid):return None
        return {'id':cid,'shop_id':self.sid,'status':self.campaign_status,
                'days':[{'id':self.did,'campaign_id':cid,'shop_id':self.sid,
                         'review_status':self.day_status}]}
    def assets(self, token, sid, ids):
        return token=='signed-owner-jwt' and sid==self.sid and ids==[self.media]

class FakeStore:
    def __init__(self):self.calls=[];self.accept=True
    def list_day_designs(self, token, sid, cid, did):
        self.calls.append(('read',token,sid,cid,did));return []
    def list_models(self, token, sid, tenant):
        self.calls.append(('models',token,sid));return []
    def save_design(self, token, sid, cid, did, doc, **kw):
        self.calls.append(('save',token,sid,cid,did,kw))
        if not self.accept:return None
        return {'design_id':str(uuid4()),'revision':1,
                'server_document_sha256':'a'*64}

class Feature3ApiTests(unittest.TestCase):
    def setUp(self):
        self.sid,self.cid,self.did=[str(uuid4()) for _ in range(3)]
        self.tenant=FakeTenant(self.sid,self.cid,self.did)
        self.store=FakeStore()
        self.api=Feature3V2API(self.tenant,self.store)
        self.uid=str(uuid4())
        self.document={'schema':'retailgrowth.poster.v2','shop_id':self.sid,
                       'format':'square','template':'fashion',
                       'background':'#FFFFFF','layers':[{'id':'brand','type':'text',
                       'x':0.1,'y':0.1,'w':0.8,'h':0.2,'color':'#000000',
                       'text':'Shop','font_size':26,'bold':True}]}
        self.body={'design':self.document,'expected_revision':0}
    def call(self,method='POST',body=None,cid=None,did=None):
        return self.api.day('signed-owner-jwt',self.uid,cid or self.cid,
                            did or self.did,method,self.body if body is None else body)
    def test_owner_can_save_private_draft_only_and_read_history(self):
        status,doc=self.call()
        self.assertEqual(status,201)
        self.assertEqual(doc['status'],'DRAFT')
        self.assertFalse(doc['rendered'])
        self.assertEqual(self.store.calls[0][0],'save')
        self.assertEqual(self.call('GET')[0],200)
    def test_denials_owner_viewer_other_shop_and_wrong_campaign(self):
        self.tenant.role='VIEWER'
        self.assertEqual(self.call()[0],404)
        self.tenant.role='OWNER'
        self.assertEqual(self.call(cid=str(uuid4()))[0],404)
        self.assertEqual(self.call(did=str(uuid4()))[0],404)
        self.tenant.day_status='APPROVED'
        self.assertEqual(self.call()[0],404)
        self.tenant.day_status='DRAFT'
        self.tenant.campaign_status='FAILED'
        self.assertEqual(self.call()[0],404)
        self.tenant.campaign_status='DRAFT'
        self.store.accept=False
        self.assertEqual(self.call()[0],409)
    def test_reject_document_claims_and_unsafe_revisions(self):
        self.assertEqual(self.call(body={**self.body,'status':'APPROVED'})[0],400)
        self.assertEqual(self.call(body={**self.body,'expected_revision':True})[0],400)
        self.assertEqual(self.call(body={**self.body,'design':{**self.document,'shop_id':str(uuid4())}})[0],400)
        self.assertEqual(self.call(body={**self.body,'design':{**self.document,'image_url':'https://evil.invalid'}})[0],400)
        self.assertEqual(self.call(body={**self.body,'expected_revision':2})[0],400)
        self.assertEqual(self.store.calls,[])
    def test_approved_catalog_route_denies_other_user(self):
        self.assertEqual(self.api.models('signed-owner-jwt',self.uid,self.sid)[0],200)
        self.tenant.role='SUSPENDED'
        self.assertEqual(self.api.models('signed-owner-jwt',self.uid,self.sid)[0],404)

if __name__=='__main__': unittest.main()
