"use client";

import { useEffect, useMemo, useState } from "react";
import { getSupabaseBrowser } from "@/lib/supabase-browser";

type Theme = "이해하기 어려운 우리" | "지금의 나" | "미래의 우리";
type Response = { thought: string; outward: string; wish: string };
type Card = { id: string; theme: Theme; number: string; title: string; question: string; prompts: [string, string, string] };
type Credentials = { sessionId: string; accessToken: string; joinCode?: string };
type Member = { id: string; display_name: string };
type AnswerStatus = "draft" | "ready" | "published";
type Answer = { cardId: string; memberId: string; status: AnswerStatus; response?: Response };
type SessionState = { currentMemberId: string; members: Member[]; answers: Answer[] };

const cards: Card[] = [
  { id: "understanding-1", theme: "이해하기 어려운 우리", number: "01", title: "설명하기 어려운 나", question: "가까운 사람에게도 말로 옮기기 어려운 내 모습은 뭐야?", prompts: ["그 모습은 주로 어떤 순간에 나타나?", "다른 사람은 그 모습을 어떻게 오해하기 쉬울까?", "상대가 이 모습에 대해 꼭 알아주었으면 하는 건 뭐야?"] },
  { id: "understanding-2", theme: "이해하기 어려운 우리", number: "02", title: "마음이 닿지 않을 때", question: "내 감정이 상대에게 잘 닿지 않는다고 느끼는 순간은 어떤 때야?", prompts: ["그때 내 마음에는 어떤 생각이 따라와?", "상대가 모를 수 있는 내 감정의 크기는 어느 정도야?", "바로 이해하지 못해도, 어떤 태도라면 덜 혼자라고 느낄까?"] },
  { id: "understanding-3", theme: "이해하기 어려운 우리", number: "03", title: "내게는 당연한 것", question: "나에게는 너무 당연하지만, 상대에게는 낯설 수 있는 마음의 기준은 뭐야?", prompts: ["그 기준은 내게 왜 당연하게 느껴질까?", "그 기준이 어긋났을 때 나는 어떤 의미로 받아들이기 쉬워?", "이 기준을 이해시키기 위해 어떤 이야기를 들려주고 싶어?"] },
  { id: "understanding-4", theme: "이해하기 어려운 우리", number: "04", title: "곁에 있는 방식", question: "상대가 달라지지 않아도, 내가 ‘내 곁에 있구나’라고 느끼는 순간은 언제야?", prompts: ["그 순간 상대는 무엇을 하고 있거나 하지 않고 있을까?", "그 행동이 내게 주는 안심은 어떤 모습이야?", "내가 그 마음을 알아차렸을 때 어떻게 전하고 싶어?"] },
  { id: "understanding-5", theme: "이해하기 어려운 우리", number: "05", title: "억지로 바라지 않는 것", question: "상대가 나를 위해 애쓰더라도, 억지로 바뀌거나 무리하지 않았으면 하는 부분은 뭐야?", prompts: ["왜 그 모습을 억지로 바꾸지 않았으면 해?", "그 모습 안에서 내가 이미 좋아하는 점은 뭐야?", "대신 서로가 오해하지 않기 위해 나눌 수 있는 말은 뭐야?"] },
  { id: "understanding-6", theme: "이해하기 어려운 우리", number: "06", title: "함께 머물 마음", question: "바로 해결하지 못해도, 상대와 함께 바라보고 싶은 내 마음은 뭐야?", prompts: ["혼자 감당할 때 가장 어려운 지점은 뭐야?", "누군가 곁에 있을 때 달라지는 건 무엇이야?", "이 마음을 꺼낼 때 상대에게 바라는 분위기는 뭐야?"] },
  { id: "present-1", theme: "지금의 나", number: "07", title: "요즘의 나", question: "요즘 내 마음을 가장 많이 차지하는 것은 무엇이야?", prompts: ["그 마음은 언제 특히 커져?", "그 마음이 내 하루를 어떻게 바꾸고 있어?", "상대가 지금 알아주면 좋겠는 건 뭐야?"] },
  { id: "present-2", theme: "지금의 나", number: "08", title: "혼자 있을 때", question: "혼자 있을 때의 나는 다른 사람들과 있을 때와 무엇이 가장 달라?", prompts: ["혼자일 때 가장 자연스럽게 하는 일은 뭐야?", "그 모습은 왜 평소에 잘 보이지 않을까?", "상대가 그 모습을 알게 되면 무엇을 이해해 주면 좋겠어?"] },
  { id: "present-3", theme: "지금의 나", number: "09", title: "조용한 노력", question: "요즘 내가 조용히 해내고 있는데, 알아주면 좋겠는 노력은 뭐야?", prompts: ["그 노력은 언제부터 이어지고 있어?", "그 과정에서 가장 힘들거나 뿌듯한 순간은 뭐야?", "누군가 알아봐 준다면 어떤 말이 가장 힘이 될까?"] },
  { id: "present-4", theme: "지금의 나", number: "10", title: "나를 지키는 것", question: "아무리 가까운 관계 안에서도 내가 지키고 싶은 나만의 시간·기준·공간은 뭐야?", prompts: ["그것이 내게 중요한 이유는 뭐야?", "그것이 지켜지지 않을 때 나는 어떻게 달라져?", "상대가 오해하지 않도록 어떤 말로 설명하고 싶어?"] },
  { id: "present-5", theme: "지금의 나", number: "11", title: "되돌아오는 곳", question: "기분이 복잡할 때 나를 다시 나답게 만들어 주는 것은 뭐야?", prompts: ["그것을 하면 내 마음은 어떻게 달라져?", "혼자 하고 싶은지, 누군가와 하고 싶은지 궁금해.", "상대가 도와줄 수 있는 방식이 있다면 뭐야?"] },
  { id: "present-6", theme: "지금의 나", number: "12", title: "아직 남은 말", question: "요즘 자주 떠오르지만 아직 충분히 말하지 못한 생각은 뭐야?", prompts: ["그 생각은 언제 특히 자주 떠올라?", "말로 꺼내기 어려운 이유는 뭐야?", "상대가 어떤 방식으로 물어봐 주면 이야기하기 쉬울까?"] },
  { id: "future-1", theme: "미래의 우리", number: "13", title: "완벽한 휴일", question: "몇 년 뒤의 완벽한 휴일을 상상하면, 어떤 장면이 가장 먼저 떠올라?", prompts: ["그 하루는 어디에서, 누구와 시작되고 있을까?", "그 하루에서 가장 오래 느끼고 싶은 감정은 뭐야?", "그 휴일이 너에게 이상적인 이유는 뭐야?"] },
  { id: "future-2", theme: "미래의 우리", number: "14", title: "지키고 싶은 일상", question: "삶이 아무리 바빠져도 우리에게 꼭 있었으면 하는 평범한 일상은 뭐야?", prompts: ["그 일상은 하루의 어느 때에 있을까?", "그 시간에 우리는 어떤 기분이었으면 해?", "그 평범함이 우리에게 중요한 이유는 뭐야?"] },
  { id: "future-3", theme: "미래의 우리", number: "15", title: "나만의 꿈", question: "언젠가 꼭 해보고 싶은 내 꿈은 무엇이고, 그 삶에 상대는 어떤 모습으로 함께하면 좋겠어?", prompts: ["그 꿈은 내게 어떤 의미야?", "혼자 이루는 것과 함께 응원받는 것은 어떻게 다를까?", "상대가 어떤 마음으로 지켜봐 주면 좋겠어?"] },
  { id: "future-4", theme: "미래의 우리", number: "16", title: "함께 이루고 싶은 것", question: "우리 둘이 함께 목표 하나를 이룰 수 있다면, 무엇이 가장 설렐 것 같아?", prompts: ["그 목표를 떠올리면 어떤 장면이 그려져?", "혼자가 아니라 둘이어서 더 좋은 이유는 뭐야?", "그 목표를 향해 지금부터 해보고 싶은 작은 일은 뭐야?"] },
  { id: "future-5", theme: "미래의 우리", number: "17", title: "기억되고 싶은 장면", question: "몇 년 뒤에도 기억하고 싶은 지금의 우리 모습은 어떤 장면일까?", prompts: ["그 장면 속 우리는 무엇을 하고 있을까?", "그때의 어떤 분위기나 말이 기억에 남을 것 같아?", "그런 순간을 더 만들기 위해 바라는 게 있어?"] },
  { id: "future-6", theme: "미래의 우리", number: "18", title: "우리에게 남길 말", question: "미래의 우리에게 지금 한 문장을 남긴다면, 어떤 말을 건네고 싶어?", prompts: ["그 문장은 지금의 우리에게 왜 필요한 말일까?", "그 말을 읽는 미래의 우리는 어떤 모습이었으면 해?", "그 미래를 위해 지금 서로에게 전하고 싶은 마음은 뭐야?"] }
];

const themes: Theme[] = ["이해하기 어려운 우리", "지금의 나", "미래의 우리"];
const blankResponse: Response = { thought: "", outward: "", wish: "" };
// v2 deliberately ignores the anonymous-session cache used before login existed.
const storageKey = "between-us-session-v2";
const answerKeys: (keyof Response)[] = ["thought", "outward", "wish"];

function responseReady(response: Response) {
  return answerKeys.every((key) => response[key].trim().length > 0);
}

function statusLabel(answer?: Answer, partnerExists = true) {
  if (!partnerExists) return "입장 대기";
  if (!answer) return "아직 시작 전";
  if (answer.status === "draft") return "작성 중";
  if (answer.status === "ready") return "답변 완료";
  return "공개됨";
}

export default function Home() {
  const [stage, setStage] = useState<"welcome" | "login" | "setup" | "join" | "created" | "journey" | "answer">("welcome");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [activeCardId, setActiveCardId] = useState(cards[0].id);
  const [draft, setDraft] = useState<Response>(blankResponse);
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const activeCard = cards.find((card) => card.id === activeCardId) ?? cards[0];
  const currentMember = sessionState?.members.find((member) => member.id === sessionState.currentMemberId);
  const partner = sessionState?.members.find((member) => member.id !== sessionState.currentMemberId);
  const answers = useMemo(() => sessionState?.answers ?? [], [sessionState]);
  const ownAnswer = answers.find((answer) => answer.cardId === activeCard.id && answer.memberId === sessionState?.currentMemberId);
  const partnerAnswer = answers.find((answer) => answer.cardId === activeCard.id && answer.memberId !== sessionState?.currentMemberId);

  useEffect(() => {
    const stored = window.localStorage.getItem(storageKey);
    if (!stored) return;
    try {
      const saved = JSON.parse(stored) as Credentials;
      if (saved.sessionId && saved.accessToken) {
        setCredentials(saved);
        setStage("journey");
      }
    } catch { window.localStorage.removeItem(storageKey); }
  }, []);

  useEffect(() => {
    const supabase = getSupabaseBrowser();
    void supabase.auth.getSession().then(({ data }) => setAuthToken(data.session?.access_token ?? ""));
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setAuthToken(session?.access_token ?? "");
      if (session) setStage("setup");
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (credentials) window.localStorage.setItem(storageKey, JSON.stringify(credentials));
  }, [credentials]);

  useEffect(() => { window.scrollTo(0, 0); }, [stage]);

  useEffect(() => {
    if (!credentials) return;
    void loadSession(true);
    const timer = window.setInterval(() => { void loadSession(true); }, 4000);
    return () => window.clearInterval(timer);
  }, [credentials]);

  useEffect(() => {
    if (!dirty || !credentials || ownAnswer?.status === "published") return;
    const timer = window.setTimeout(() => { void saveDraft(); }, 850);
    return () => window.clearTimeout(timer);
  }, [dirty, draft, activeCardId, credentials, ownAnswer?.status]);

  async function loadSession(silent = false) {
    if (!credentials) return;
    try {
      const response = await fetch("/api/sessions/state", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${authToken}` }, body: JSON.stringify(credentials) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setSessionState(data);
      if (!silent) setError("");
    } catch (caught) {
      if (!silent) setError(caught instanceof Error && caught.message === "SESSION_NOT_AVAILABLE" ? "이 세션을 찾을 수 없거나 만료되었어요." : "세션 상태를 불러오지 못했어요.");
    }
  }

  async function createSession() {
    if (!name.trim()) return;
    setLoading(true); setError("");
    try {
      const response = await fetch("/api/sessions/create", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${authToken}` }, body: JSON.stringify({ name }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setCredentials({ sessionId: data.sessionId, accessToken: data.accessToken, joinCode: data.joinCode });
      setJoinCode(data.joinCode);
      setStage("created");
    } catch { setError("세션을 만들지 못했어요. 잠시 후 다시 시도해 주세요."); }
    finally { setLoading(false); }
  }

  async function joinSession() {
    if (!name.trim() || !joinCode.trim()) return;
    setLoading(true); setError("");
    try {
      const response = await fetch("/api/sessions/join", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${authToken}` }, body: JSON.stringify({ name, joinCode }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setCredentials({ sessionId: data.sessionId, accessToken: data.accessToken, joinCode });
      setStage("journey");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "JOIN_FAILED";
      setError(message === "SESSION_FULL" ? "이미 두 사람이 들어와 있는 세션이에요." : "코드를 찾을 수 없거나 만료되었어요.");
    } finally { setLoading(false); }
  }

  function openCard(card: Card) {
    const existing = answers.find((answer) => answer.cardId === card.id && answer.memberId === sessionState?.currentMemberId);
    setActiveCardId(card.id);
    setDraft(existing?.response ?? blankResponse);
    setDirty(false);
    setError("");
    setStage("answer");
  }

  async function saveDraft() {
    if (!credentials || ownAnswer?.status === "published") return false;
    setSaving(true);
    try {
      const response = await fetch("/api/sessions/answers", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${authToken}` }, body: JSON.stringify({ ...credentials, cardId: activeCard.id, response: draft }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setDirty(false);
      await loadSession(true);
      return true;
    } catch { setError("초안을 저장하지 못했어요. 인터넷 연결을 확인해 주세요."); return false; }
    finally { setSaving(false); }
  }

  async function publishAnswer() {
    if (!credentials || !responseReady(draft)) return;
    setLoading(true); setError("");
    try {
      if (dirty && !(await saveDraft())) return;
      const response = await fetch("/api/sessions/publish", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${authToken}` }, body: JSON.stringify({ ...credentials, cardId: activeCard.id }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      await loadSession(true);
    } catch { setError("답변을 공개하지 못했어요. 잠시 후 다시 시도해 주세요."); }
    finally { setLoading(false); }
  }

  async function sendMagicLink() {
    setLoading(true); setError("");
    const { error: authError } = await getSupabaseBrowser().auth.signInWithOtp({ email, options: { emailRedirectTo: window.location.origin } });
    setLoading(false); setError(authError ? "로그인 링크를 보내지 못했어요." : "이메일의 로그인 링크를 열어 주세요.");
  }

  if (stage === "welcome") return <main className="shell"><nav className="nav"><span className="mark">◇</span><span>between us</span><span className="nav-note">한 세션 안에서 함께 쓰기</span></nav><section className="hero"><p className="eyebrow">ONE SHARED SESSION</p><h1>같은 시간 안에서,<br /><em>서로의 마음을 써요.</em></h1><p className="hero-copy">세션 코드 하나로 둘이 들어와 각자의 답을 적어요.<br />작성 중인 마음은 보이되, 내용은 내가 공개할 때까지 비공개예요.</p><button className="primary" onClick={() => setStage(authToken ? "setup" : "login")}>우리 세션 만들기 <span>→</span></button></section></main>;

  if (stage === "login") return <main className="shell centered"><nav className="nav"><span className="mark">◇</span><span>between us</span></nav><section className="form-card"><p className="eyebrow">SIGN IN TO RETURN ANYWHERE</p><h1>이메일로<br />내 세션을 지켜요</h1><label>이메일<input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" type="email" /></label><button className="primary" disabled={!email || loading} onClick={sendMagicLink}>{loading ? "보내는 중…" : "로그인 링크 받기"} <span>→</span></button>{error && <p className="error-note centered-note">{error}</p>}</section></main>;

  if (stage === "setup") return <main className="shell centered"><nav className="nav"><span className="mark">◇</span><span>between us</span></nav><section className="form-card"><p className="eyebrow">START A SESSION</p><h1>카드에 쓸<br />내 이름</h1><label>이름 또는 서로 부르는 별명<input value={name} onChange={(event) => setName(event.target.value)} placeholder="예: 민지" maxLength={16} /></label><button className="primary" disabled={!name.trim() || loading} onClick={createSession}>{loading ? "세션 만드는 중…" : "새 세션 만들기"} <span>→</span></button><button className="text-button" onClick={() => setStage("join")}>받은 세션 코드가 있어요</button>{error && <p className="error-note centered-note">{error}</p>}</section></main>;

  if (stage === "join") return <main className="shell centered"><nav className="nav"><span className="mark">◇</span><span>between us</span></nav><section className="form-card"><p className="eyebrow">JOIN A SESSION</p><h1>같은 대화 안으로<br />들어갈게요.</h1><label>이름 또는 서로 부르는 별명<input value={name} onChange={(event) => setName(event.target.value)} placeholder="예: 민지" maxLength={16} /></label><label>받은 세션 코드<input className="code-input" value={joinCode} onChange={(event) => setJoinCode(event.target.value)} placeholder="예: A1B2-C3D4-E5F6" autoCapitalize="characters" /></label><button className="primary" disabled={!name.trim() || !joinCode.trim() || loading} onClick={joinSession}>{loading ? "입장하는 중…" : "세션 입장하기"} <span>→</span></button><button className="text-button" onClick={() => setStage("setup")}>새 세션 만들기</button>{error && <p className="error-note centered-note">{error}</p>}</section></main>;

  if (stage === "created") return <main className="shell handover-shell"><nav className="nav"><span className="mark">◇</span><span>between us</span></nav><section className="handover"><p className="eyebrow">YOUR SESSION IS READY</p><span className="seal">✓</span><h1>둘만의 세션이<br />열렸어요.</h1><p>이 코드를 상대에게 전해 주세요.<br />상대가 입장하면 같은 카드 여정에서 만나게 돼요.</p><button className="share-code" onClick={() => navigator.clipboard?.writeText(joinCode)}>{joinCode}<small>눌러서 코드 복사</small></button><button className="primary" onClick={() => setStage("journey")}>내 여정 시작하기 <span>→</span></button></section></main>;

  if (stage === "answer") {
    const ownPublished = ownAnswer?.status === "published";
    return <main className="shell answer-shell"><nav className="nav"><span className="mark">◇</span><span>between us</span><span className="nav-note">{activeCard.theme} · 카드 {activeCard.number}</span></nav><section className="answer-card"><div className="card-kicker"><span>{activeCard.number}</span><b>{activeCard.theme}</b></div><h1>{activeCard.title}</h1><p className="situation">{activeCard.question}</p><div className="private-note"><span>◌</span> 상대에게는 {statusLabel(ownAnswer, Boolean(partner))} 상태만 보여요. 내용은 공개 전까지 나만 볼 수 있어요.</div>{activeCard.prompts.map((prompt, index) => { const key = answerKeys[index]; return <label key={key}>{prompt}<textarea value={draft[key]} disabled={ownPublished} onChange={(event) => { setDraft({ ...draft, [key]: event.target.value }); setDirty(true); }} placeholder="떠오르는 생각을 자유롭게 적어 주세요." maxLength={240} /></label>; })}{partnerAnswer?.status === "published" && <section className="after-card"><div><p className="eyebrow">{partner?.display_name ?? "상대"}의 공개된 답</p><h2>{partner?.display_name ?? "상대"}가 먼저<br />마음을 열었어요.</h2></div>{activeCard.prompts.map((prompt, index) => <p key={prompt}><b>{prompt}</b><br />{partnerAnswer.response?.[answerKeys[index]]}</p>)}</section>}<div className="answer-actions"><button className="ghost" onClick={() => setStage("journey")}>여정으로 돌아가기</button>{ownPublished ? <span className="notice">내 답변을 공개했어요.</span> : <button className="primary" disabled={!responseReady(draft) || loading || saving} onClick={publishAnswer}>{loading ? "공개하는 중…" : "내 답변 공개하기"} <span>→</span></button>}</div>{saving && <p className="notice">초안 저장 중…</p>}{!ownPublished && responseReady(draft) && !saving && <p className="notice">답변 완료. 공개는 원할 때만 눌러 주세요.</p>}{error && <p className="error-note">{error}</p>}</section></main>;
  }

  return <main className="shell"><nav className="nav"><span className="mark">◇</span><span>between us</span><span className="nav-note">{currentMember?.display_name ?? "우리"}의 공동 여정</span></nav><section className="library-head"><p className="eyebrow">ONE SESSION · TWO PRIVATE VOICES</p><h1>어려운 마음부터,<br /><em>함께 천천히.</em></h1><p>{partner ? <>{partner.display_name}와 같은 세션에 있어요. 답변 내용은 각자가 공개하기 전까지 보이지 않아요.</> : <>상대가 아직 입장하지 않았어요. 세션 코드를 전해 주세요.</>}</p>{credentials?.joinCode && <button className="share-code" onClick={() => navigator.clipboard?.writeText(credentials.joinCode ?? "")}>{credentials.joinCode}<small>상대에게 세션 코드 전하기</small></button>}{error && <p className="error-note">{error}</p>}</section><div className="deck">{themes.map((theme) => <section className="theme-section" key={theme}><div className="theme-title"><h2>{theme}</h2><span>6장</span></div><div className="card-grid">{cards.filter((card) => card.theme === theme).map((card) => { const mine = answers.find((answer) => answer.cardId === card.id && answer.memberId === sessionState?.currentMemberId); const theirs = answers.find((answer) => answer.cardId === card.id && answer.memberId !== sessionState?.currentMemberId); return <button className={`moment-card ${mine?.status === "published" ? "done" : ""}`} onClick={() => openCard(card)} key={card.id}><span>{card.number}</span><strong>{card.title}</strong><small>{card.question}</small><small>나: {statusLabel(mine, true)}</small><small>상대: {statusLabel(theirs, Boolean(partner))}</small></button>; })}</div></section>)}</div></main>;
}
