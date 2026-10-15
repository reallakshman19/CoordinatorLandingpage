"""WP7 read-only JSON input and receipt projection; fail closed on untrusted commits."""
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

REPO="reallakshman19/CoordinatorLandingpage"
ID=re.compile(r"^OI-(\d{8})-(\d{6})-([0-9a-f]{4})$")
SHA=re.compile(r"^[0-9a-f]{40}$")
ASSOCIATED={"OWNER","MEMBER","COLLABORATOR"}
FIELDS={"id","project","target","type","text","replaces","created_at"}
RECEIPT_FIELDS={"input","state","at","by","note","links"}
STATES={"ACK","NEEDS_CLARIFICATION","HANDLED"}
LINK=re.compile(r"^https://github\.com/([\w.-]+/[\w.-]+)/(?:"
                r"(?:issues|pull)/\d+(?:#issuecomment-\d+)?|"
                r"blob/[0-9a-f]{40}/logs/[\w.-]+/"
                r"(?:inputs/OI-\d{8}-\d{6}-[0-9a-f]{4}\.json|receipts\.jsonl)(?:#L\d+)?)$")


def timestamp(v):
    try:
        value=dt.datetime.fromisoformat(v.replace("Z","+00:00"))
        return value.astimezone(dt.timezone.utc) if value.tzinfo else None
    except (AttributeError,ValueError,TypeError):
        return None


def linked_repo(url,registered):
    m=LINK.fullmatch(url) if isinstance(url,str) else None
    return bool(m and m.group(1) in registered)


def registries(root):
    projects={}
    for p in sorted((Path(root)/"logs").glob("*/registry.json")):
        row=json.loads(p.read_text(encoding="utf-8"))
        if (not isinstance(row,dict) or row.get("project")!=p.parent.name
                or not re.fullmatch(r"[\w.-]+",p.parent.name)):
            raise ValueError("invalid registered project")
        projects[p.parent.name]=row.get("repository")
    return projects


def github_provenance(repo,path):
    """Read associated GitHub author, not spoofable JSON or git user.name.

    A GitHub commit API author association is established by owner login or
    verified collaborator permission; otherwise it is UNKNOWN, not Owner.
    """
    def api(url):
        try:
            p=subprocess.run(["gh","api",url],check=True,text=True,capture_output=True)
            return json.loads(p.stdout)
        except (OSError,ValueError,subprocess.CalledProcessError):
            return None
    rows=api(f"/repos/{repo}/commits?path={quote(path,safe='/')}&per_page=1")
    if not isinstance(rows,list) or len(rows)!=1:
        return {"sha":None,"author":None,"association":"UNKNOWN"}
    row=rows[0]
    author=row.get("author") if isinstance(row,dict) else None
    login=author.get("login") if isinstance(author,dict) else None
    sha=row.get("sha") if isinstance(row,dict) else None
    if not login or not isinstance(sha,str) or not SHA.fullmatch(sha):
        return {"sha":None,"author":None,"association":"UNKNOWN"}
    association="OWNER" if login.lower()==repo.split("/")[0].lower() else "UNKNOWN"
    if association=="UNKNOWN":
        permission=api(f"/repos/{repo}/collaborators/{quote(login)}/permission")
        if isinstance(permission,dict) and permission.get("permission") in ("admin","maintain","write"):
            association="COLLABORATOR"
    return {"sha":sha,"author":login,"association":association}


def schema_errors(obj,name,project,registered):
    errors=[]
    if not isinstance(obj,dict):
        obj={}
    if set(obj)!=FIELDS:
        errors.append("schema_keys")
    key=obj.get("id")
    m=ID.fullmatch(key) if isinstance(key,str) else None
    if not m or key!=name:
        errors.append("id_or_path_mismatch")
    if obj.get("project")!=project or project not in registered:
        errors.append("project_or_path_mismatch")
    if not isinstance(obj.get("target"),str) or not 1<=len(obj["target"])<=160:
        errors.append("target")
    if not isinstance(obj.get("type"),str) or not 1<=len(obj["type"])<=64:
        errors.append("type")
    if not isinstance(obj.get("text"),str) or not 1<=len(obj["text"])<=1500:
        errors.append("text")
    repl=obj.get("replaces")
    if repl is not None and (not isinstance(repl,str) or not ID.fullmatch(repl)):
        errors.append("replaces")
    instant=timestamp(obj.get("created_at"))
    if not instant or (m and instant.strftime("%Y%m%d-%H%M%S")!=m.group(1)+"-"+m.group(2)):
        errors.append("created_at")
    return sorted(set(errors))


def read_committed_inputs(root,repo=REPO,resolver=None):
    reg=registries(root)
    accepted={repo}|{r for r in reg.values() if isinstance(r,str)}
    resolve=resolver or github_provenance
    records=[]
    for project in sorted(reg):
        folder=Path(root)/"logs"/project
        receipt_path=folder/"receipts.jsonl"
        receipt_meta=resolve(repo,receipt_path.relative_to(root).as_posix()) if receipt_path.is_file() else {}
        receipt_trusted=(receipt_meta.get("association") in ASSOCIATED
                         and bool(SHA.fullmatch(receipt_meta.get("sha") or "")))
        receipts={}
        if receipt_path.is_file():
            for lineno,line in enumerate(receipt_path.read_text(encoding="utf-8").splitlines(),1):
                try:
                    row=json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row,dict) or not isinstance(row.get("input"),str) or not ID.fullmatch(row["input"]):
                    continue
                valid=(set(row)==RECEIPT_FIELDS and row.get("state") in STATES
                       and timestamp(row.get("at")) is not None
                       and isinstance(row.get("by"),str) and bool(row["by"].strip())
                       and isinstance(row.get("note"),str)
                       and isinstance(row.get("links"),list)
                       and all(linked_repo(u,accepted) for u in row["links"])
                       and (row["state"]!="HANDLED" or bool(row["links"])))
                # Latest line wins, even if invalid: an invalid newer receipt
                # MUST NOT leave an older HANDLED result effective.
                receipts[row["input"]]=(row,lineno) if valid and receipt_trusted else None
        for path in sorted((folder/"inputs").glob("*.json")):
            try:
                obj=json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                obj={}
            if not isinstance(obj,dict):
                obj={}
            name=path.stem
            errors=schema_errors(obj,name,project,reg)
            local=path.relative_to(root).as_posix()
            provenance=resolve(repo,local)
            trusted=provenance.get("association") in ASSOCIATED
            sha=provenance.get("sha") if isinstance(provenance.get("sha"),str) and SHA.fullmatch(provenance["sha"]) else None
            file_url=f"https://github.com/{repo}/blob/{sha}/{local}" if sha else None
            created=obj.get("created_at")
            steps={"posted":{"url":file_url,"at":created} if file_url and timestamp(created) else None,
                   "ack":None,"sent":None,"evidence":None,"check":None,"result":None}
            status="NEEDS_CLARIFICATION" if errors or not trusted else "OPEN"
            receipt=None
            chosen=receipts.get(name)
            if chosen and trusted and not errors:
                row,lineno=chosen
                status="ACKNOWLEDGED" if row["state"]=="ACK" else row["state"]
                url=(f"https://github.com/{repo}/blob/{receipt_meta['sha']}/"
                     f"logs/{project}/receipts.jsonl#L{lineno}")
                steps["ack" if status=="ACKNOWLEDGED" else "result"]={
                    "url":url,"at":row["at"],"accepted":status=="HANDLED"}
                if status=="HANDLED":
                    receipt=url
            reason=(errors[0] if errors else ("unverified_commit_author" if not trusted else None))
            why=("This saved JSON does not match the required format: "+", ".join(errors)+"."
                 if errors else ("The GitHub commit author is not verified for this repository."
                 if not trusted else ("A linked result is recorded; this is not Owner approval."
                 if status=="HANDLED" else "Waiting for the team to record a linked result.")))
            records.append({
                "id":name,"number":None,"source_kind":"json_file",
                "issue_url":file_url,"source_commit":sha,"source_author":provenance.get("author"),
                "author_association":provenance.get("association") if trusted else "UNKNOWN",
                "is_outsider":not trusted,
                "author_classification":"ASSOCIATED_NOT_OWNER_PROOF" if trusted else "OUTSIDER",
                "project":obj.get("project") if not errors else "",
                "target":obj.get("target") if isinstance(obj.get("target"),str) else "",
                "type":obj.get("type") if isinstance(obj.get("type"),str) else "OWNER_INPUT",
                "text":obj.get("text","")[:300] if isinstance(obj.get("text"),str) else "",
                "ts":created,"status":status,"state":status.lower(),
                "needs_you":trusted and status not in ("HANDLED","SUPERSEDED"),
                "receipt":receipt,"replaces":obj.get("replaces"),
                "reason":reason,"flags":errors+(["unverified_commit_author"] if not trusted else []),
                "superseded_by":None,"authority":"UNVERIFIED","effective":False,
                "review":{"state":"UNVERIFIED"},"protected_action":False,
                "trace":{"steps":steps,"why":why,
                         "waiting_for":None if status=="HANDLED" else ("Owner" if errors else "TeamCoordinator")},
            })
    index={row["id"]:row for row in records}
    for row in records:
        old=index.get(row["replaces"])
        if (old and old is not row and row["project"]==old["project"]
                and not row["is_outsider"] and not old["is_outsider"] and not row["flags"]):
            old.update(status="SUPERSEDED",state="superseded",
                       needs_you=False,superseded_by=row["id"],receipt=None)
    return records
