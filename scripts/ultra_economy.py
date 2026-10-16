"""UltraEconomyMode v1: read-only TASK START / TASK EVIDENCE / Next Move link.

No GitHub writes, agent launches, timer creation or authority transitions.
The project registry opts in with ultra_economy: {enabled: true, max_cycles: 1..5}.
"""
from datetime import datetime, timedelta, timezone
import re

ID8 = re.compile(r"^[0-9a-f]{8}$")
TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
START = re.compile(
    r"^TASK START v1\s*·\s*(?P<project>[^·\n]+)\s*·\s*"
    r"(?P<role>[^·\n]+)\s*·\s*chat\s+(?P<id8>[0-9a-f]{8})\s*·\s*"
    r"task\s+(?P<task>[A-Za-z0-9_.-]+)\s*·\s*"
    r"cycle\s+(?P<cycle>\d+)/(?P<limit>\d+)\s*$", re.MULTILINE)
END = re.compile(
    r"^TASK EVIDENCE v2\s*·\s*(?P<project>[^·\n]+)\s*·\s*"
    r"(?P<role>[^·\n]+)\s*·\s*chat\s+(?P<id8>[0-9a-f]{8})\s*·",
    re.MULTILINE)


def when(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def field(body, name):
    match = re.search(r"^" + re.escape(name) + r":\s*(.+)$",
                      body, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def status(body):
    """Normalize claims, never convert a claim into independently VERIFIED."""
    value = field(body, "Status")
    if not value:
        match = re.search(r"^Task:[^\n]*?\bStatus:\s*(.*)$", body, re.I | re.M)
        value = match.group(1).strip() if match else ""
    # Compound statuses such as 'DONE engineering / review pending' are claims.
    for category in ("FAILED", "BLOCKED", "PARTIAL", "DONE"):
        if re.search(r"\b" + category + r"\b", value, re.I):
            return category
    return "UNKNOWN"


def config(registry):
    cfg = registry.get("ultra_economy")
    if not isinstance(cfg, dict) or cfg.get("enabled") is not True:
        return {"enabled": False, "max_cycles": None, "error": None}
    limit = cfg.get("max_cycles")
    if type(limit) is not int or not 1 <= limit <= 5:
        return {"enabled": False, "max_cycles": None, "error": "invalid_max_cycles"}
    return {"enabled": True, "max_cycles": limit, "error": None}


def _comments(threads, issue, repository):
    thread=threads.get(issue)
    if not isinstance(thread,dict) or thread.get("number")!=issue or thread.get("repository")!=repository:
        return None
    rows=thread.get("comments")
    return rows if isinstance(rows,list) else None


def _agent_source(agent):
    url=agent.get("evidence_thread_url") or agent.get("evidence_thread") or ""
    m=re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d+)",url)
    return (m.group(1),int(m.group(2)),url) if m else None


def _binding(row,issue_url,bindings):
    """Independent immutable registry anchor for a GitHub comment, fail closed."""
    import hashlib
    if not isinstance(row,dict) or type(row.get("id")) is not int or row["id"]<=0:
        return None
    body=row.get("body")
    updated=when(row.get("updated_at"))
    created=when(row.get("created_at"))
    if not isinstance(body,str) or not updated or not created or updated<created:
        return None
    url=issue_url+"#issuecomment-"+str(row["id"])
    expected=bindings.get(str(row["id"]))
    digest=hashlib.sha256(body.encode("utf-8")).hexdigest()
    if not isinstance(expected,dict) or expected.get("url")!=url or (
            expected.get("comment_id")!=row["id"] or
            expected.get("updated_at")!=row["updated_at"] or
            expected.get("body_sha256")!=digest):
        return None
    return {"url":url,"comment_id":row["id"],"updated_at":row["updated_at"],
            "body_sha256":digest}


def _find_rows(rows,pattern,project,id8,role):
    found=[]
    for row in rows:
        if not isinstance(row,dict):continue
        body=row.get("body")
        marker=pattern.search(body) if isinstance(body,str) else None
        if marker and (marker.group("project").strip(),marker.group("id8"),
                       marker.group("role").strip())==(project,id8,role):
            found.append((row,body,marker))
    return found


def _start_records(rows,project,id8,role,max_cycles,issue_url,bindings):
    starts,warnings=[],[]
    counts={}
    for row,body,match in _find_rows(rows,START,project,id8,role):
        task=match.group("task");cycle=int(match.group("cycle"))
        key=(task,cycle)
        counts[key]=counts.get(key,0)+1
        bind=_binding(row,issue_url,bindings)
        stamped=when(row.get("created_at"))
        planned=field(body,"Planned outcome")
        expected=field(body,"Expected next")
        blocker=field(body,"Known blocker")
        workplan=field(body,"Workplan")
        declared=int(match.group("limit"))
        if not bind:
            warnings.append("source_binding_invalid_or_missing")
        if (not TASK_ID.fullmatch(task) or declared!=max_cycles or
                not 1<=cycle<=max_cycles or not stamped or
                not all((planned,expected,blocker,workplan)) or
                not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/\d+",workplan)):
            warnings.append("invalid_task_start")
            continue
        starts.append({"task":task,"cycle":cycle,"max_cycles":max_cycles,
            "start_comment_id":row["id"],"started_at":stamped.isoformat(),
            "planned_outcome":planned[:500],"expected_next":expected[:500],
            "known_blocker":blocker[:500],"workplan":workplan,
            "timer_claim":field(body,"Fallback")[:200],"fallback":"NOT_ARMED",
            "fallback_due_at":None,"start_binding":bind,
            "start_binding_valid":bool(bind)})
    if any(n>1 for n in counts.values()):warnings.append("duplicate_task_start")
    # Chronology is source order, not iteration order or a restart-local counter.
    starts.sort(key=lambda x:(x["started_at"],x["start_comment_id"]))
    return starts,sorted(set(warnings)),counts


def _end_for_start(rows,start,project,id8,role,issue_url,bindings):
    stamped=when(start["started_at"])
    candidates=[]
    for row,body,marker in _find_rows(rows,END,project,id8,role):
        at=when(row.get("created_at"))
        if not at or at<stamped:continue
        task=field(body,"Task").split(maxsplit=1)[0] if field(body,"Task") else ""
        if task!=start["task"] or field(body,"UEM cycle")!=str(start["cycle"])+"/"+str(start["max_cycles"]):
            continue
        candidates.append((at,row,body))
    if len(candidates)>1:return None,"duplicate_task_end"
    if not candidates:return None,None
    at,row,body=candidates[0]
    bind=_binding(row,issue_url,bindings)
    if not bind:return None,"source_binding_invalid_or_missing"
    return {"end_comment_id":row["id"],"ended_at":at.isoformat(),
            "end_binding":bind,"claim_status":status(body),
            "not_done":field(body,"Not done / HOLD")[:500],
            "next_claim":field(body,"Next")[:500]},None


def _find_move(moves,evidence_url,current,id8,head=None):
    matches=[]
    for move in moves or []:
        if not isinstance(move,dict) or move.get("class")!="Dispatch":continue
        trigger=move.get("trigger") or {}
        basis=move.get("basis") or {}
        if not isinstance(trigger,dict):continue
        if ((move.get("to") or {}).get("id8")==id8
                and trigger.get("type")=="uem_end"
                and trigger.get("task")==current["task"]
                and trigger.get("cycle")==current["cycle"]
                and trigger.get("end_comment_id")==current["end_comment_id"]
                and basis.get("evidence")==evidence_url):
            matches.append(move)
    if len(matches)!=1:return None,("AMBIGUOUS_MOVE" if matches else "NO_MATCHING_MOVE")
    move=matches[0]
    if "stale basis" in (move.get("flags") or []) or (head and (
            (move.get("basis") or {}).get("head") or "").lower()!=head.lower()):
        return move,"STALE_MOVE"
    if move.get("state") in ("SEND_INTENT","DELIVERY_UNCERTAIN"):
        return move,"DELIVERY_UNCERTAIN"
    if move.get("state") in ("SENT_TO_CHAT","PICKED_UP","ACKED"):
        return move,"DELIVERED_MOVE"
    if move.get("state") in ("HELD","REJECTED","CANCELLED","SUPERSEDED","EXPIRED"):
        return move,"MOVE_HELD_OR_CLOSED"
    return move,"AWAITING_DELIVERY"


def _followup(end_at,now):
    at=when(end_at)
    if not at or now<at:return {"state":"UNKNOWN","next_due_at":None}
    for minutes in (15,20,30):
        due=at+timedelta(minutes=minutes)
        if now<due:return {"state":"WAITING","next_due_at":due.isoformat()}
    return {"state":"OVERDUE_30","next_due_at":None}


def _grant(cfg,agent,id8,now):
    """Monitoring entitlement NEVER confers execution; check both separately."""
    monitoring=(cfg.get("monitoring_grants") or {}).get(id8)
    execution=(cfg.get("execution_grants") or {}).get(id8)
    def checked(value,purpose):
        if not isinstance(value,dict) or value.get("verified") is not True:
            return "UNVERIFIED_"+purpose
        if value.get("holder_id8")!=id8 or value.get("project")!=cfg.get("_project"):
            return "WRONG_HOLDER_"+purpose
        expires=when(value.get("expires_at"))
        if expires is None or expires<=now:return "EXPIRED_"+purpose
        return "VALID"
    return checked(monitoring,"MONITORING"),checked(execution,"EXECUTION")


def _execution_guard(registry,agent,id8,now,cfg):
    if (registry.get("control") or {}).get("hold"):return "HOLD"
    state=str(agent.get("status") or "").lower()
    if "retired" in state or "stop" in state or "hold" in state:return "RETIRED_OR_STOPPED"
    if not state.startswith("active"):return "NOT_ACTIVE"
    adoption=str(agent.get("adoption") or "").upper()
    if adoption in ("PENDING","NOT_VERIFIED","UNQUALIFIED","REJECTED"):
        return "UNQUALIFIED_SUCCESSOR"
    if agent.get("qualified_successor") is False or agent.get("material_release") is False:
        return "UNQUALIFIED_SUCCESSOR"
    monitor,exec_state=_grant({**cfg,"_project":registry.get("project")},agent,id8,now)
    if exec_state!="VALID":return exec_state
    leases=(registry.get("writer_leases") or [])+(registry.get("leases") or [])
    for lease in leases:
        if not isinstance(lease,dict):continue
        if lease.get("exclusive") is not True or not (
                lease.get("active") is True or
                str(lease.get("state")).upper()=="ACTIVE"):
            continue
        # An active exclusive lease with unknown custody is a conflict too.
        actor=str(lease.get("actor") or "")
        owner=lease.get("holder_id8") or (actor if ID8.fullmatch(actor) else None)
        if owner!=id8:return "WRITER_LEASE_CONFLICT"
    return None


def project(registry,agents,threads,next_view,now=None):
    """Read-only projection; no task is working before immutable source/grant check."""
    opts=config(registry)
    result={"enabled":opts["enabled"],"max_cycles":opts["max_cycles"],
            "error":opts["error"],"agents":{},"timer":"NOT_ARMED"}
    if not opts["enabled"]:return result
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("now must be timezone aware")
    cfg=registry.get("ultra_economy") or {}
    bindings=cfg.get("source_bindings") or {}
    for agent in agents:
        id8=agent.get("chat_id8")
        if not isinstance(id8,str) or not ID8.fullmatch(id8):continue
        # Key the read-only projection by id8; duplicate roster identities
        # must never silently approve competing working claims.
        if id8 in result["agents"]:
            result["agents"][id8]={"state":"AMBIGUOUS_ROSTER","may_proceed":False}
            continue
        # Source-fenced before any claim: an agent in a projected UI list is
        # not an authorized roster row. The owning registry must explicitly
        # register this instance, without duplicate id8 or stale role/status.
        source=_agent_source(agent)
        if not source or source[0]!=registry.get("repository"):
            # No foreign-project ghost agent may appear as a work candidate.
            continue
        roster=registry.get("agents")
        if not isinstance(roster,list):
            result["agents"][id8]={"state":"MISSING_ROSTER_ROW","may_proceed":False}
            continue
        matches=[x for x in roster if isinstance(x,dict) and
                 x.get("chat_id8")==id8]
        if len(matches)>1:
            result["agents"][id8]={"state":"AMBIGUOUS_ROSTER","may_proceed":False}
            continue
        if not matches or matches[0].get("role")!=agent.get("role"):
            result["agents"][id8]={"state":"MISSING_ROSTER_ROW","may_proceed":False}
            continue
        if (str(matches[0].get("status") or "")!=str(agent.get("status") or "")
                or matches[0].get("adoption")!=agent.get("adoption")
                or matches[0].get("qualified_successor")!=agent.get("qualified_successor")):
            result["agents"][id8]={"state":"STALE_ROSTER_PROJECTION","may_proceed":False}
            continue
        guard=_execution_guard(registry,matches[0],id8,now,cfg)
        monitor,execution=_grant({**cfg,"_project":registry.get("project")},agent,id8,now)
        basis={"monitoring_grant":monitor,"execution_grant":execution,
               "timer":"NOT_ARMED"}
        if guard:
            result["agents"][id8]={"state":guard,"may_proceed":False,**basis}
            continue
        rows=_comments(threads,source[1],source[0])
        if rows is None:
            result["agents"][id8]={"state":"UNKNOWN_SOURCE","may_proceed":False,**basis}
            continue
        starts,warnings,counts=_start_records(rows,registry.get("project"),id8,
                                              agent.get("role"),opts["max_cycles"],
                                              source[2],bindings)
        if not starts:
            result["agents"][id8]={"state":"NO_TASK_START","may_proceed":False,
                                    "warnings":warnings,**basis}
            continue
        current=starts[-1]
        # Preserve the earliest declaration for diagnostics when duplicates
        # exist; the ambiguity always blocks execution, not a winner choice.
        if "duplicate_task_start" in warnings:
            current=next((x for x in starts if
                          (x["task"],x["cycle"])==(
                              current["task"],current["cycle"])),current)
        item={**current,"warnings":warnings,"may_proceed":False,
              "monitoring_grant":monitor,"execution_grant":execution,
              "fallback":"NOT_ARMED","timer":"NOT_ARMED"}
        if "duplicate_task_start" in warnings:
            item.update(state="AMBIGUOUS_START")
            result["agents"][id8]=item;continue
        if ("source_binding_invalid_or_missing" in warnings or
                "invalid_task_start" in warnings or
                not current["start_binding_valid"]):
            item.update(state="SOURCE_BINDING_INVALID")
            result["agents"][id8]=item;continue
        # The workplan/task identifier survives a chat restart and a successor
        # id8. A per-agent key would incorrectly replenish consumed cycles.
        ledger_key=current["workplan"]+"|"+current["task"]
        ledger=(cfg.get("cycle_ledger") or {}).get(ledger_key) or {}
        completed=ledger.get("completed_cycles",0) if isinstance(ledger,dict) else 0
        if type(completed) is not int or completed<0 or current["cycle"]!=completed+1:
            item["state"]="UEM_CYCLE_RESTART_OR_GAP"
            result["agents"][id8]=item;continue
        item["cycle_balance"]={"uem_completed":completed,
                               "uem_remaining":opts["max_cycles"]-completed,
                               "next_move_task_count":(next_view.get("task_cycle") or {}).get("count"),
                               "owner_delegation_cycle":"SEPARATE_UNVERIFIED"}
        end,problem=_end_for_start(rows,current,registry.get("project"),id8,
                                   agent.get("role"),source[2],bindings)
        if problem:
            item.update(state=("AMBIGUOUS_END" if problem=="duplicate_task_end"
                               else "SOURCE_BINDING_INVALID"))
        elif end is None:
            item["state"]="WORKING_CLAIM"
        else:
            item.update(end)
            item["fallback"]="NOT_ARMED"
            head=(agent.get("evidence_head_status") or {}).get("current_head")
            move,condition=_find_move(next_view.get("moves"),source[2],item,id8,head)
            item["move_state"]=condition
            item["move_id"]=move.get("id") if move else None
            item["followup"]=(_followup(end["ended_at"],now) if monitor=="VALID"
                              else {"state":"MONITORING_UNGRANTED","next_due_at":None})
            exhausted=current["cycle"]>=opts["max_cycles"]
            # At the final pilot cycle, source hazards remain visible.
            # A one-cycle limit denies continuation; it must not conceal an
            # unresolved SEND_INTENT or stale/ambiguous delivered move.
            if condition in ("DELIVERY_UNCERTAIN","STALE_MOVE","AMBIGUOUS_MOVE",
                             "MOVE_HELD_OR_CLOSED"):
                item["state"]=condition
            elif exhausted:item["state"]="MAX_CYCLES_REACHED"
            elif condition=="DELIVERED_MOVE" and end["claim_status"]!="UNKNOWN":
                item["state"]="NEXT_MOVE_RECORDED_DELIVERED"
                item["may_proceed"]=True
            else:item["state"]=condition
            if exhausted or condition in ("DELIVERED_MOVE","MOVE_HELD_OR_CLOSED"):
                item["followup"]={"state":"STOPPED","next_due_at":None}
        result["agents"][id8]=item
    return result
