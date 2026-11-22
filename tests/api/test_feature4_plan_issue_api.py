"""Real saved F2 content -> server-owned unapproved F4 proposal and JWT route.

These fakes do not assert hosted DB migrations, actual signed images, or
billing. The source candidate separately has true SQL tenant tests.
"""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_plan_issue_api import Feature4PlanIssueAPI  # noqa: E402
from feature2_saved_campaign_proposal import saved_campaign_creative_proposal  # noqa: E402
from http_api import HTTPAPI  # noqa: E402
from security import AuthenticationError  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "99999999-9999-4999-8999-999999999999"
USER = "22222222-2222-4222-8222-222222222222"
CID = "33333333-3333-4333-8333-333333333333"
DAY = "44444444-4444-4444-8444-444444444444"
MEDIA = "55555555-5555-4555-8555-555555555555"
PLAN = "66666666-6666-4666-8666-666666666666"


def campaign():
    return {"id":CID,"shop_id":SHOP,"status":"DRAFT","days":[{
        "id":DAY,"campaign_id":CID,"shop_id":SHOP,"review_status":"DRAFT",
        "instagram":{"reel":{"duration_seconds":30,"aspect_ratio":"9:16",
             "cta":"Visit our boutique", "music_asset_id":None,
             "storyboard":[
                 {"start_seconds":0,"duration_seconds":15,"asset_id":MEDIA,
                  "overlay_text":"New arrivals"},
                 {"start_seconds":15,"duration_seconds":15,"asset_id":MEDIA,
                  "overlay_text":"Visit our boutique"},
             ]}}
    }]}


def media():
    return [{"id":MEDIA,"shop_id":SHOP,"storage_bucket":"retailgrowth-media",
             "source":"UPLOAD","license_name":"owned","mime_type":"image/png",
             "object_path":SHOP+"/uploads/"+MEDIA+".png"}]


class RLSUsers:
    def __init__(self):
        self.active=True
        self.reel=campaign()
        self.stills=media()
        self.reads=0

    def campaign(self, token, user_id, campaign_id):
        return self.reel if token=="signed-A" and user_id==USER and campaign_id==CID else None

    def member(self, token, user_id, shop_id, *, write=False):
        return self.active and token=="signed-A" and user_id==USER and shop_id==SHOP

    def _request(self, table, token, *, query=None):
        assert table=="media_assets" and token=="signed-A"
        assert query["shop_id"]=="eq."+SHOP and query["id"]=="in.("+MEDIA+")"
        self.reads+=1
        return copy.deepcopy(self.stills)


class ServiceStore:
    def __init__(self):
        self.records={}
        self.inserts=0
        self.ack_lost=False

    def request(self, path, *, query=None, data=None, method="GET"):
        assert path=="feature4_creative_plans"
        if method=="GET":
            return [row for row in self.records.values()
                    if row["shop_id"]=="11111111-1111-4111-8111-111111111111"
                    and "eq."+row["proposal_sha256"]==query["proposal_sha256"]]
        assert method=="POST"
        self.inserts+=1
        assert data["state"]=="DRAFT" and data["issued_by"]==USER
        assert data["proposal"]["approved"] is False
        assert data["media_asset_ids"]==[MEDIA]
        item={"id":PLAN,"shop_id":SHOP,"campaign_id":CID,
              "proposal_sha256":data["proposal_sha256"],"state":"DRAFT"}
        self.records[data["proposal_sha256"]]=item
        if self.ack_lost:
            raise ExceptionForAckLoss("HTTP response lost")
        return [item]


class ExceptionForAckLoss(Exception):
    pass


def signed(token):
    if token=="signed-A":
        return USER
    raise AuthenticationError("bad JWT")


def setup():
    users,admin=RLSUsers(),ServiceStore()
    api=HTTPAPI(signed,users,feature4_issue_api=Feature4PlanIssueAPI(users,admin))
    return api,users,admin


def test_real_server_saved_copy_issues_one_unapproved_review_only_no_provider():
    api,users,admin=setup()
    request=f"/campaigns/{CID}/feature4-plans"
    code,result=api.handle("POST",request,"Bearer signed-A",{"day_id":DAY})
    assert code==201
    assert result["plan_id"]==PLAN
    assert result["shop_id"]==SHOP
    assert result["status"]=="DRAFT"
    assert admin.inserts==1 and users.reads==1
    saved=list(admin.records.values())[0]
    assert saved["proposal_sha256"]==result["proposal_sha256"]
    assert api.handle("POST",request,"Bearer signed-A",{"day_id":DAY})==(201,result)
    assert admin.inserts==1
    proposal=saved_campaign_creative_proposal(campaign(),DAY,media())
    assert proposal["proposal_sha256"]==result["proposal_sha256"]
    assert proposal["proposal"]["script"]["approved"] is False
    assert proposal["proposal"]["music_asset_id"] is None
    assert proposal["proposal"]["source_reel"]==campaign()["days"][0]["instagram"]["reel"]
    assert proposal["proposal"]["scenes"][-1]["headline"]=="Visit our boutique"


def test_no_forged_user_or_shop_can_insert_creative_plan():
    api,users,admin=setup()
    route=f"/campaigns/{CID}/feature4-plans"
    assert api.handle("POST",route,"Bearer forged",{"day_id":DAY})[0]==401
    assert api.handle("POST",route,"Bearer signed-A",{
        "day_id":DAY,"approved":True})[0]==400
    assert api.handle("POST",route,"Bearer signed-A",{"day_id":OTHER})[0]==404
    users.active=False
    assert api.handle("POST",route,"Bearer signed-A",{"day_id":DAY})[0]==403
    users.active=True
    users.stills[0]["shop_id"]=OTHER
    assert api.handle("POST",route,"Bearer signed-A",{"day_id":DAY})[0]==409
    assert admin.inserts==0


def test_foreign_or_unlicensed_media_and_unapproved_music_never_write():
    for alteration in ("license","path","music","text","gap","status"):
        api,users,admin=setup()
        if alteration=="license": users.stills[0]["license_name"]="unknown"
        if alteration=="path": users.stills[0]["object_path"]=OTHER+"/uploads/"+MEDIA+".png"
        if alteration=="music": users.reel["days"][0]["instagram"]["reel"]["music_asset_id"]=MEDIA
        if alteration=="text": users.reel["days"][0]["instagram"]["reel"]["storyboard"][0]["overlay_text"]="Changed<unsafe>"
        if alteration=="gap": users.reel["days"][0]["instagram"]["reel"]["storyboard"][1]["start_seconds"]=16
        if alteration=="status": users.reel["status"]="PLANNING"
        status,_=api.handle("POST",f"/campaigns/{CID}/feature4-plans",
                             "Bearer signed-A",{"day_id":DAY})
        assert status==409,(alteration,status)
        assert admin.inserts==0


def test_default_disabled_cannot_submit_source_only_client_fields():
    users,admin=RLSUsers(),ServiceStore()
    api=HTTPAPI(signed,users)
    assert api.handle("POST",f"/campaigns/{CID}/feature4-plans",
                      "Bearer signed-A",{"day_id":DAY})==(503,{"error":"FEATURE4_PLAN_ISSUE_DISABLED"})
    assert not admin.records
