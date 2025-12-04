# -*- coding: utf-8 -*-
import os
import re
import ast
import json
from typing import Tuple

# ===== APIキー配線 =====
# 優先順位: 環境変数 OPENAI_API_KEY（必須）
from openai import OpenAI as _OpenAI
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY が未設定です。例: export OPENAI_API_KEY='sk-xxxxx'")

client = _OpenAI(api_key=_OPENAI_API_KEY)

# ===== モデル設定 =====
DEFAULT_MODEL = "gpt-5"              # 通常回答
SEARCH_MODEL = "gpt-5-search-api"    # 検索前提モデル（存在しない環境では gpt-4o-search-preview にフォールバック）

# ===== Google CSE（任意） =====
_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""
_CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID") or ""

# =========================================================
# 1) “検索はモデル判断”版（Responses + web_search）
# =========================================================
def request_ChatGPT_latest(promptText: str, isAnnouceJudge: bool = False) -> Tuple[bool, str]:
    """
    GPT‑5 Responses API を用いて応答を生成します。新しい API 仕様に合わせて
    text.format を使用し、応答のフォーマットを指定します。
    Responses API が失敗した場合は chat completions API へフォールバックします。
    """
    systemPrompt = (
        "あなたはセキュリティリサーチャーの優秀なアシスタントです。"
        if isAnnouceJudge
        else "あなたはセキュリティリサーチャーの優秀なアシスタントです。"
             "自分の知識が不足している場合はWeb検索等の外部情報源で補完してください。"
    )

    retIsSuccess = False
    retText = ""

    try:
        # Responses API を試す（新形式の text.format を使用）
        try:
            resp = client.responses.create(
                model=DEFAULT_MODEL,
                instructions=systemPrompt,
                input=promptText,
                tools=[{"type": "web_search"}],
                tool_choice="auto",
                max_output_tokens=2000,
                text={"format": {"type": "text"}}
            )
            # output_text または content から結果を取り出す
            retText = (getattr(resp, "output_text", "") or "").strip()
            if not retText:
                for item in (getattr(resp, "output", []) or []):
                    for content_item in (item.content or []):
                        if content_item.type in ("output_text", "text") and content_item.text:
                            retText = content_item.text.strip()
                            break
                    if retText:
                        break
            retIsSuccess = True
        except Exception:
            # Responses API が失敗した場合は Chat Completions にフォールバック
            resp = client.chat.completions.create(
                model=SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": systemPrompt},
                    {"role": "user", "content": promptText},
                ],
                max_tokens=2000,
            )
            retText = (resp.choices[0].message.content or "").strip()
            retIsSuccess = True
    except Exception as e:
        retText = f"生成AIによる回答生成に失敗しました。詳細: {e}"
        retIsSuccess = False

    return retIsSuccess, retText

# =========================================================
# 2) gpt-5-search-api を使う版（Chat Completions：毎回検索）
# =========================================================
def request_ChatGPT_latest_searchAPI(promptText: str, isAnnouceJudge: bool=False) -> Tuple[bool, str]:
    """
    Chat Completions + 検索特化モデルを用いて、常にWeb検索を前提に回答させる版。
    署名: (str, bool) -> (bool, str)  ※関数名/引数は不変更
    """
    retIsSuccess, retText = False, ""
    try:
        systemPrompt = (
            "あなたはセキュリティリサーチャーの優秀なアシスタントです。"
            if isAnnouceJudge else
            "あなたはセキュリティリサーチャーの優秀なアシスタントです。"
            "今から企業情報を渡すので、質問とルールを正確に理解し、ルールに従って回答してください。"
            "不足分はWeb検索で根拠（出典）付きで補完してください。"
        )

        try:
            resp = client.chat.completions.create(
                model=SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": systemPrompt},
                    {"role": "user", "content": promptText},
                ],
                max_tokens=2000,
            )
        except Exception as e:
            msg = str(e).lower()
            # モデル未検出時は gpt-4o-search-preview にフォールバック
            if ("model" in msg) and ("not found" in msg or "unknown" in msg):
                resp = client.chat.completions.create(
                    model="gpt-4o-search-preview",
                    messages=[
                        {"role": "system", "content": systemPrompt},
                        {"role": "user", "content": promptText},
                    ],
                    max_tokens=2000,
                )
            else:
                raise

        retText = (resp.choices[0].message.content or "").strip()
        retIsSuccess = True

    except Exception as e:
        retText = f"生成AIによる回答生成に失敗しました。詳細: {e}"
        retIsSuccess = False
    return retIsSuccess, retText


# =========================================================
# 3) OpenAI Vision（そのまま）
# =========================================================
def request_openai_vision_latest(
    prompt_text: str = "",
    base64_data: str | None = None,
    image_path: str = "",
    model: str = "gpt-4.1",
):
    """
    OpenAI Responses API で画像+テキストを投げて解析結果のテキストを返す。
    """
    import base64
    import requests

    if not prompt_text:
        prompt_text = (
            "この画像には英字が書いてあります。なんと書いてありますか？"
            "英字として読み取れる文字だけ教えてください。"
            "回答は必ず「文字列: <なんと書いてあるか>」の形式で。"
        )

    def encode_image_to_base64(path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    if base64_data is None:
        if not image_path:
            return "image_path か base64_data のどちらかを指定してください。"
        base64_data = encode_image_to_base64(image_path)

    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt_text},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_data}"},
                ],
            }
        ],
        "max_output_tokens": 1200,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_OPENAI_API_KEY}",
    }

    try:
        import requests
        resp = requests.post("https://api.openai.com/v1/responses", headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        text_out = ""
        for item in (data.get("output") or []):
            if item.get("type") == "message" and item.get("role") == "assistant":
                for c in (item.get("content") or []):
                    if c.get("type") in ("output_text", "text") and "text" in c:
                        text_out += c["text"]
        text_out = (text_out or "").strip()
        if text_out.startswith("文字列:"):
            text_out = text_out[len("文字列:"):].strip()
        return text_out or "（空の応答でした）"
    except Exception:
        return "生成AIによる回答生成に失敗しました。(CAPTCHA)"


# =========================================================
# 4) Google CSE（任意：ある場合のみ使用）
# =========================================================
def googleCustomSearch(keyword):
    if not (_GOOGLE_API_KEY and _CUSTOM_SEARCH_ENGINE_ID):
        return []
    try:
        from time import sleep
        from googleapiclient.discovery import build
        service = build("customsearch", "v1", developerKey=_GOOGLE_API_KEY)

        page_limit = 1
        start_index = 1
        response = []
        for n_page in range(0, page_limit):
            try:
                sleep(1)
                res = service.cse().list(
                    q=keyword,
                    cx=_CUSTOM_SEARCH_ENGINE_ID,
                    lr='lang_en',
                    num=3,
                    start=start_index
                ).execute()
                response.append(res)
                nextp = res.get("queries", {}).get("nextPage", [])
                if nextp:
                    start_index = nextp[0].get("startIndex", 0)
                else:
                    break
            except Exception:
                break
        return response
    except Exception:
        return []


# =========================================================
# 5) 文字処理ユーティリティ
# =========================================================
def fullwidth_to_halfwidth(text: str) -> str:
    return text.translate(str.maketrans({
        '：': ':',
        '’': "'",
        '，': ',',
        '（': '(',
        '）': ')',
        '｛': '{',
        '｝': '}',
        '［': '[',
        '］': ']',
        '　': ' ',
    }))

def clean_url(text: str) -> str:
    if not text:
        return text
    textTmp = text.replace("[.]", ".").strip()
    url_pattern = re.compile(r"(https?://[^\s/]+|www\.[^\s/]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
    m = url_pattern.search(textTmp)
    return m.group(0) if m else textTmp

def _extract_json_or_text_from_responses(resp) -> str:
    """
    Responses APIの戻りから、テキスト or JSON文字列を取り出す。
    - output_text が空でも、output[].content[] の text/json を優先的に拾う
    """
    # 1) まず output_text（テキスト出力がある場合のみ）
    t = getattr(resp, "output_text", None)
    if t:
        return t.strip()

    # 2) output[].content[] をたどる（SDKオブジェクト/辞書両対応）
    def _get(o, k, d=None):
        return (o.get(k, d) if isinstance(o, dict) else getattr(o, k, d))

    output = _get(resp, "output", []) or []
    for item in output:
        content = _get(item, "content", []) or []
        for c in content:
            ctype = _get(c, "type", "")
            if ctype in ("output_text", "text"):
                txt = _get(c, "text", "")
                if txt:
                    return txt.strip()
            # json_schema/structured の場合
            if "json" in (c if isinstance(c, dict) else c.__dict__):
                js = _get(c, "json", None)
                if js is not None:
                    return json.dumps(js, ensure_ascii=False)

    # 3) 念のため model_dump() を舐める
    try:
        dump = resp.model_dump() if hasattr(resp, "model_dump") else None
        if dump:
            for item in dump.get("output", []):
                for c in item.get("content", []):
                    if c.get("text"):
                        return c["text"].strip()
                    if c.get("json") is not None:
                        return json.dumps(c["json"], ensure_ascii=False)
    except Exception:
        pass
    return ""
    
# =========================================================
# 6) メイン：被害企業情報の取得（**主に修正**）
# =========================================================
def requestVictimsInfo_ChatGPT(victimsName, victimsURL=''):
    retDict = {}

    victimsURLTmp = ''
    if len(victimsURL) > 0:
        victimsURLTmp = f'({victimsURL})'

    # -------- data_string（バグ修正：カンマ抜け等） --------
    data_string = "{\
        'victimName': '企業名',\
        'victimHQLocation': '本社の所属する国',\
        'victimBizType': '業種',\
        'victimUrl': '企業のホームページURL',\
        'victimsummary': '企業の概要説明'\
    }"

    # -------- JSONスキーマ（厳格） --------
    json_schema = {
        "type": "object",
        "properties": {
            "victimName": {"type": "string"},
            "victimHQLocation": {"type": "string"},
            "victimBizType": {"type": "string"},
            "victimUrl": {"type": "string"},
            "victimsummary": {"type": "string"},
        },
        "required": ["victimName", "victimHQLocation", "victimBizType", "victimUrl", "victimsummary"],
        "additionalProperties": False
    }

    def _call_with_schema(prompt_text: str):
        """
        まず Responses API + extra_body で json_schema を渡す。
        SDK / モデルが temperature を拒否したら、temperature を外してリトライ。
        それでもダメなら chat.completions にフォールバック（同様にリトライ）。
        戻り値: (kind, resp)  # kind: "responses" | "chat"
        """
        system_instructions = (
            "あなたはセキュリティリサーチャーの優秀なアシスタントです。"
            "必ずweb_searchを実行して公式サイトと外部の独立ソースを確認し、"
            "確証が弱いものは『不明』と出力してください。"
            "推測は厳禁。日本語で、JSON以外の文字は出力しないでください。"
        )

        json_schema_body = {
            "type": "json_schema",
            "json_schema": {
                "name": "victim_profile",
                "schema": {
                    "type": "object",
                    "properties": {
                        "victimName": {"type": "string"},
                        "victimHQLocation": {"type": "string"},
                        "victimBizType": {"type": "string"},
                        "victimUrl": {"type": "string"},
                        "victimsummary": {"type": "string"},
                    },
                    "required": [
                        "victimName",
                        "victimHQLocation",
                        "victimBizType",
                        "victimUrl",
                        "victimsummary",
                    ],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }

        def _responses_try(with_temperature: bool):
            kwargs = dict(
                model=DEFAULT_MODEL,
                instructions=system_instructions,
                input=prompt_text,
                tools=[{"type": "web_search"}],
                tool_choice="auto",
                max_output_tokens=2800,
                extra_body={"response_format": json_schema_body},
            )
            if with_temperature:
                kwargs["temperature"] = 0
            return client.responses.create(**kwargs)

        def _chat_try(with_temperature: bool):
            kwargs = dict(
                model=SEARCH_MODEL,  # 例: gpt-5-search-api（無ければ上位でフォールバックする実装でも可）
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": prompt_text},
                ],
                max_tokens=1800,
                response_format=json_schema_body,
            )
            if with_temperature:
                kwargs["temperature"] = 0
            return client.chat.completions.create(**kwargs)

        # 実装してみたけどどれも例外になるからいったん保留
        skipTries = True
        if skipTries:
            # --- A案: Responses API で実行（温度あり→温度なしの順で） ---
            try:
                try:
                    resp = _responses_try(with_temperature=True)
                except Exception as e:
                    msg = str(e).lower()
                    if ("temperature" in msg and "incompatible" in msg) or ("unsupported" in msg and "temperature" in msg) or ("invalid_request_error" in msg and "temperature" in msg):
                        resp = _responses_try(with_temperature=False)
                    else:
                        raise
                return ("responses", resp)
            except Exception:
                pass  # Chat 側にフォールバック

            # --- B案: Chat Completions で実行（同様に温度あり→なし） ---
            try:
                try:
                    resp = _chat_try(with_temperature=True)
                except Exception as e:
                    msg = str(e).lower()
                    if ("temperature" in msg and "incompatible" in msg) or ("unsupported" in msg and "temperature" in msg) or ("invalid_request_error" in msg and "temperature" in msg):
                        resp = _chat_try(with_temperature=False)
                    else:
                        # 例：SEARCH_MODEL が存在しない場合など。ここでフォールバックしてもOK
                        # 任意: gpt-4o-search-preview へ切替
                        # resp = client.chat.completions.create(..., model="gpt-4o-search-preview", ...)
                        raise
                return ("chat", resp)
            except Exception as e:
                # 上位の再試行ループに任せる
                raise e
        else:
            resp = _chat_try(with_temperature=False)

    def extract_json_str_from_responses(resp) -> str:
        """
        Responses API の戻りから、JSON文字列を取り出すユーティリティ。
        - json_schema 指定時は output_text が空になるため、output[..].content[..].json を優先。
        - それが無ければ text 系を拾う。
        - 最後の手段として model_dump() を舐める。
        """
        # 1) まず output_text（テキスト出力がある場合のみ）
        txt = getattr(resp, "output_text", None)
        if txt:
            return txt.strip()

        # 2) SDKのオブジェクト形式／辞書形式の両対応で辿る
        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        output = _get(resp, "output", [])
        if output:
            for item in output:
                content = _get(item, "content", []) or []
                for c in content:
                    ctype = _get(c, "type", None)
                    # ★ 構造化（json_schema）のときはここに入る
                    if ctype in ("output_json", "json_schema", "output_structured"):
                        js = _get(c, "json", None)
                        if js is not None:
                            # dict → 文字列
                            return json.dumps(js, ensure_ascii=False)
                    # テキストのときはこちら
                    if ctype in ("output_text", "text"):
                        t = _get(c, "text", None)
                        if t:
                            return t.strip()

        # 3) 念のためのフォールバック：model_dump() を総なめ
        try:
            dump = resp.model_dump() if hasattr(resp, "model_dump") else (
                resp if isinstance(resp, dict) else None
            )
            if dump:
                for item in dump.get("output", []):
                    for c in item.get("content", []):
                        if "json" in c and c["json"] is not None:
                            return json.dumps(c["json"], ensure_ascii=False)
                        if "text" in c and c["text"]:
                            return c["text"].strip()
        except Exception:
            pass

        # 4) 何も取れない場合は空文字
        return ""

    # -------- プロンプト（表記ゆれ/別名/ドメイン強制） --------
    def _build_prompt(vName: str, vUrlTmp: str, extra_context: str = "") -> str:
        domain_hint = ""
        url_clean = clean_url(vUrlTmp.replace("(", "").replace(")", "")) if vUrlTmp else ""
        if url_clean and "." in url_clean:
            # site: の強制ヒント
            domain_hint = f"・入力URLからドメインを抽出し、site:{url_clean} でも検索してください。"

        return fullwidth_to_halfwidth(f"""
#質問
「{vName} {vUrlTmp}」はどのような会社ですか。

#要件
・必ずweb_searchを実行し、公式サイトと外部の独立した出典を最低1つずつ確認してください。
・社名の表記ゆれ（和名/英名/省略/旧社名/現地法人）を考慮（例: 天龍, 天龍製鋸, Tenryu, Tenryu America, Tenryu Co., Ltd. など）。
{domain_hint}
・以下の項目を【業種リスト】の定義で出力してください。
  - 企業名（victimName）
  - 本社の所属する国（victimHQLocation）
  - 業種（victimBizType）
  - 企業のホームページURL（victimUrl）
  - 企業が主にどのような業務を行っているかの概要説明（victimsummary）

【業種リスト】
医療/運輸/エネルギー/教育/金融・保険/サービス/食品/製造/その他業種/地方行政機関/鉄鋼/不動産/法律/卸売・小売/観光・娯楽/建設・建築/公共/工業/慈善事業/情報通信/政府機関/農林水産
・業種は必ず【業種リスト】から最も近いものを1つ選ぶ（不明なら『その他業種』）。
・事実のみに基づく。確証がない項目は『不明』と記載。
・出力は次のDict形式（Pythonでパース可能）で、**JSON以外の文字列は一切出さない**こと:
{data_string}

{extra_context}
""").strip()

    # -------- Google CSE結果（任意） --------
    googleSearchResultText = ""
    try:
        victimsNameForGoogle = clean_url(victimsName)
        victimsURLForGoogle = clean_url(victimsURL)
        if _GOOGLE_API_KEY and _CUSTOM_SEARCH_ENGINE_ID:
            googleSearchResult = googleCustomSearch(f'{victimsNameForGoogle} {victimsURLForGoogle}')
            infoNum = 1
            for resultsByPage in googleSearchResult:
                for result in resultsByPage.get('items', []):
                    title = result.get('title', '')
                    link = result.get('link', '')
                    googleSearchResultText += f'情報{infoNum}: [Title:{title}] [Link:({link})]\n'
                    infoNum += 1
    except Exception:
        googleSearchResultText = ""

    # -------- 実コール（最大3回） --------
    prompts = [
        _build_prompt(victimsName, victimsURLTmp),
        _build_prompt(victimsName, victimsURLTmp,
            "再試行: 和名/英名/略称/現地法人/旧社名の候補を広げ、"
            "headquarters/address/location のキーワードも併用して検索してください。"),
        _build_prompt(victimsName, victimsURLTmp,
            f"再試行2: 以下はGoogle検索の参考候補です。一致度の高いもののみ利用してください。\n{googleSearchResultText}") if googleSearchResultText else None,
    ]
    prompts = [p for p in prompts if p]

    data_dict = {}
    for p in prompts:
        try:
            kind, resp = _call_with_schema(p)

            if kind == "responses":
                text = extract_json_str_from_responses(resp)  # ★ここを変更
            else:  # "chat"
                text = (resp.choices[0].message.content or "").strip()

            if not text:
                continue
            # schema出力はJSON（ダブルクオート）想定 → ast.literal_evalでもOK
            parsed = None
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = ast.literal_eval(text)
            # キー存在/最低限の妥当性
            if isinstance(parsed, dict) and all(k in parsed for k in
               ("victimName", "victimHQLocation", "victimBizType", "victimUrl", "victimsummary")):
                # 後処理: URL整形/全角→半角
                parsed["victimUrl"] = clean_url(parsed.get("victimUrl", ""))
                for k in parsed.keys():
                    if isinstance(parsed[k], str):
                        parsed[k] = fullwidth_to_halfwidth(parsed[k].strip())
                data_dict = parsed
                break
        except Exception as e:
            print(str(e))
            continue

    # 失敗時は空dictを返す（呼び元踏襲）
    if not data_dict:
        return retDict

    # ====== ここから既存の後続ロジック（日本との関係/アナウンス判定） ======
    try:
        if len(data_dict.get('victimName', '')) > 0 and len(data_dict.get('victimBizType', '')) > 0:
            if '不明' not in data_dict['victimName'] and '不明' not in data_dict['victimBizType']:
                victimsNamebyAI = data_dict['victimName']
                promptText = (
                    f'あなたは企業調査の優秀なアシスタントです。「{victimsName} {victimsURLTmp}」が次のいずれかに該当するかを調べてください：'
                    '※いずれにも該当しない場合は{victimsNamebyAI}をもとに調査してください'
                    '1. 日本国内に子会社・関連会社・支店・研究所などの拠点を持っている。'
                    '2. 日本企業（公開会社・非公開会社問わず）や日本政府機関、日本に本社を置く国際企業と資本提携・合弁・包括的な事業提携を結んでいる。'
                    '3. 日本の主要産業（製造業、金融、医療、公共インフラなど）や医療関連事業に深く関わる取引実績がある。'

                    '調査時には、企業名の和英・略称・旧社名など表記揺れを考慮し、商業登記、企業の公式発表、信頼性の高いニュース記事や業界レポートなど複数の独立した情報源を優先してください。関係が疑われる場合には、その根拠となる具体的な情報源（例：報道記事のタイトルや公的な発表）を必ず示してください。明確な証拠が得られない、情報が矛盾している、または疑いの段階を超えない場合は「不明」としてください。'
                    '調査は最大3回行い、最も正確な情報を提供してください。'

                    '回答は以下の形式に従ってください（変更不可）：'
                    '- 日本企業との明確な関係があると判断できる場合：最初に「あり。」と書き、具体的な関係性を続けて200文字以内で説明する。'
                    '- 明確な関係がない、または判断できない場合：最初に「不明。」と書き、必要に応じて疑いの根拠や調査結果を簡潔に述べる。'
                    '- 全文を日本語で記述する。'
                )

                isSuccess, retText = request_ChatGPT_latest(promptText)
                retText = (retText or "").strip()
                if isSuccess and '不明' not in (retText or ''):
                    data_dict['victimsRelationJP'] = retText

        # 被害企業を調査できているってことは求めるアナウンス分ではないはず
        if '不明' in data_dict.get('victimName', ''):
            promptText = (
                'あなたはセキュリティ研究者の優秀なアシスタントです。'
                f'質問：「{victimsName}」が脅迫文書や、犯罪グループによるアナウンスかどうかを判断してください。'
                '回答のルール：'
                '以下の場合は、"ExtraInfo:AIによれば"から回答を開始し、どのような意味を持つ文章かを解説してください。'
                '・他の攻撃グループとの協業を示唆するような文章の場合'
                '・これから政府機関や超巨大企業などの国際的に非常に重要な組織に攻撃を仕掛けるなどの宣言の場合'
                '・攻撃グループや、彼らが使用するマルウェアをアップデートするといった宣言の場合'
                '・明らかにアナウンスの意味を持つ文章の場合'
                '以下の場合は"FALSE"のみ回答してください。'
                '・脅迫文書やアナウンスではない場合'
                '・アナウンスかどうか判断できない場合'
                '・「～を攻撃した」やただの固有名詞と思われる、情報を公表するような声明にあたらない場合'
                '・渡された文字列がドメイン名や会社名を表す場合、また意味をなさない文字列の場合'
                'これらのルールを順守し、ハルシネーションを避け、事実のみ回答してください。'
                'また、回答に「回答します」などあなたの返事は不要なので絶対に入れず、回答ルールに沿って質問に対する回答のみ返してください。'
                '回答はすべて日本語で行ってください。'
            )

            isSuccess, retText = request_ChatGPT_latest(promptText)
            retText = (retText or "").strip()
            if isSuccess and 'false' not in (retText or '').lower():
                data_dict['announcement'] = retText

    except Exception:
        pass

    if data_dict.get('victimName', ''):
        retDict = data_dict

    return retDict

# =========================================================
# 7) そのほか既存関数（軽微調整なし）
# =========================================================
def requestCheckJapaneseWord_ChatGPT(sentence, v2 = False):
    retArray = []
    try:
        promptText = f'文字列「{sentence}」に該当する日本語の単語や企業名は存在しますか？存在する場合は必ず「TRUE」のみ回答してください。存在が不明な場合は必ず「FALSE」のみ回答して下さい'
        if v2:
            promptText = (
                f'「以下の文章を解析し、日本語のローマ字読み、日本の会社名、または日本語由来の単語を抽出してください。ただし、以下の条件に従ってください：'
                f'{sentence}'
                '1. 日本に関連する強い意味を持つ外国語（例: Japan, Japanese など）は抽出対象に含める。'
                '2. 外国語としても一般的に使用される単語（例: America, memo, Kenya など）は日本語として認識しない。'
                '3. 明らかに日本語として特定可能な単語（例: sumimasen, Nihon, Suzuki, sushi など）のみを対象とする。'
                '4. 出力は、見つかった単語を「,」で区切った文字列形式にしてください。'
                '5. 該当する単語がない場合は、False と回答してください。」'
            )
        isSuccess, retText = request_ChatGPT_latest(promptText)
        retText = (retText or "").strip()
        ret = retText.split(",") if (isSuccess and ('false' not in retText.lower())) else []
    except Exception:
        ret = []
    return ret


def analyzesummaryByAI_ChatGPT(dicForMailBody):
    try:
        stringAddedSummary = ''
        stringImportantWordsInfo = ''
        stringAi_RelationJP = ''
        if (addedSummary := dicForMailBody.get('added_orgs_summary', [])):
            stringAddedSummary = json.dumps(addedSummary, ensure_ascii=False)
        if (importantWordsInfo := dicForMailBody.get('important_info', {}).get('importantWordsInfo', [])):
            stringImportantWordsInfo = json.dumps(importantWordsInfo, ensure_ascii=False)
        if (ai_RelationJP := dicForMailBody.get('important_info', {}).get('ai_RelationJP', [])):
            stringAi_RelationJP = json.dumps(ai_RelationJP, ensure_ascii=False)

        promptText = (
            f"「{stringAddedSummary}」は、今回サイト上に掲載された組織をDictionaryに整理した情報です。"
            "victimHQLocationは組織の所属国、victimBizTypeは組織の業種。"
            "これらの情報から、今回掲載された組織について、業種や国などにどのような傾向があるかを分析してください。"
            f"重要情報(重要ワード)「{stringImportantWordsInfo}」や重要情報(日本関連組織)「{stringAi_RelationJP}」が空でない場合、重要情報も併せて分析。"
            "特に日本関連組織は重要なので必ず考慮。空の場合は無視して可。"
            "不明ばかりの場合や傾向がない場合は「AIによる分析の結果、特に目立つ点はありません」。"
            "分析できる場合は「AIによる分析の結果、」から始め、200文字以内、冗長禁止、ハルシネーション禁止。"
        )
        isSuccess, retText = request_ChatGPT_latest(promptText)
        retText = (retText or "").strip()
        return retText
    except Exception:
        return ""


def isExtortioneSentence_ChatGPT(victimsName):
    ret = False
    try:
        promptText = f'「{victimsName}」はランサムウェア攻撃グループによる脅迫文章や、犯罪を示唆する文章の可能性を含みますか？その可能性を含む場合は"True"、含まない場合は"False"とだけ回答してください。'
        isSuccess, retText = request_ChatGPT_latest(promptText)
        retText = (retText or "").strip()
        if isSuccess and ('true' in (retText or '').lower()):
            ret = True
    except Exception:
        ret = False
    return ret


# --- 動作例 ---
if __name__ == "__main__":
    victimsName = 'Tenryu America'
    victimsURL = victimsURLTmp = ''
#     victimsNamebyAI = 'Toyota Motor Corporation'
    retDict = requestVictimsInfo_ChatGPT(victimsName, victimsURL='')
    print(retDict)

#     promptText = (
#         f'「{victimsName} {victimsURLTmp}」に関して、「日本企業との関係性」の調査のみを行い、それ以外の調査は不要です。'
#         f'もし「{victimsName} {victimsURLTmp}」について不明な場合は代わりに「{victimsNamebyAI}」について調査してください。'
#         '以下の要件に基づき、この組織と日本の関係性を深掘り調査してください。特に以下の点を重点的に調査し、明確な根拠を基に回答してください。'
#         '日本に子会社や活動拠点が存在するか。'
#         '日本の主要産業、政府機関、医療関連事業との具体的な関わりがあるか。'
#         '関わりのある日本関連企業や団体が明確に判明している場合は、それらを例として記述すること。'
#         '根拠が乏しく、日本関連組織との関係性を明確に説明できない場合は、以下の回答例に基づいて簡潔に回答してください。'
#         '回答例: 明確に関係があるといえる場合→一番最初に「あり。」（続けて具体的に）。 明確ではない場合一番最初に→「不明」。'
#         '具体的な関係性の説明がある場合は必ず200文字以内にまとめてください。'
#         '回答は必ず日本語で記述してください。'
#     )
#     isSuccess, retText = request_ChatGPT_latest(promptText)
    test = 1