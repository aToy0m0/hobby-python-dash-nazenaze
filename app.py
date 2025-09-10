from dash import Dash, html, dcc, Input, Output, State, callback_context
import pandas as pd
import dash_cytoscape as cyto


def create_app() -> Dash:
    app = Dash(__name__)

    # サンプル用のデータ
    df = pd.DataFrame({
        "fruit": ["Apple", "Banana", "Orange", "Grape"],
        "amount": [4, 1, 2, 3],
    })

    # サンプル画像（最大3枚）を読み込み
    import base64
    from pathlib import Path

    def _sample_images(max_count: int = 3):
        imgs = []
        folder = Path(__file__).parent / "sample-image"
        if folder.exists():
            files = sorted([p for p in folder.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}])[:max_count]
            for p in files:
                try:
                    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
                    mime = "image/png" if p.suffix.lower() == ".png" else (
                        "image/jpeg" if p.suffix.lower() in {".jpg", ".jpeg"} else "image/gif"
                    )
                    imgs.append(html.Img(src=f"data:{mime};base64,{b64}", style={"maxWidth": "32%", "height": "auto", "borderRadius": 8, "border": "1px solid #eee"}))
                except Exception:
                    pass
        return imgs

    app.layout = html.Div(
        style={"maxWidth": "100%", "margin": "24px auto", "fontFamily": "sans-serif"},
        children=[
            html.H2("Dash 最小スターター + フローチャート", style={"margin": "0 24px 16px"}),
            dcc.Tabs(id="tabs", value="sample", children=[
                dcc.Tab(label="サンプル", value="sample", children=[
                    html.Br(),
                    html.P("ドロップダウンで果物を選ぶと数量が表示されます。", style={"margin": "0 24px"}),
                    dcc.Dropdown(
                        id="fruit",
                        options=[{"label": f, "value": f} for f in df["fruit"].tolist()],
                        value="Apple",
                        clearable=False,
                        style={"width": 300, "margin": "8px 24px"},
                    ),
                    html.Div(id="amount", style={"margin": "8px 24px", "fontSize": 20}),
                    html.Div(style={"margin": "16px 24px"}, children=[
                        html.H4("実行サンプル（画像）", style={"margin": "8px 0"}),
                        html.Div(_sample_images(), style={"display": "flex", "gap": 12, "flexWrap": "wrap"}),
                    ]),
                ]),
                dcc.Tab(label="フローチャート", value="flow", children=[
                    html.Br(),
                    html.P("ノードと矢印で定義: 例) A -> B、B -> C", style={"margin": "0 24px"}),
                    # 内部状態（ノード/エッジ）を保持
                    dcc.Store(id="flow-store", data={"seq": 0, "nodes": [], "edges": []}),
                    dcc.Textarea(
                        id="flow-spec",
                        value="""Start -> Validate\nValidate -> Approve\nValidate -> Reject\nApprove -> End\nReject -> End""",
                        style={"width": "calc(100vw - 48px)", "margin": "8px 24px", "height": 140, "fontFamily": "monospace"},
                    ),
                    html.Details(open=True, style={"margin": "8px 24px", "padding": "12px", "background": "#f8fafc", "border": "1px solid #e5e7eb", "borderRadius": 8}, children=[
                        html.Summary("なぜなぜ入力（選択ノードに追加）"),
                        html.Div(style={"display": "flex", "flexDirection": "column", "gap": 8, "alignItems": "flex-start", "marginTop": 8}, children=[
                            dcc.Input(id="root-label", placeholder="課題(根本事象)", style={"width": 260}),
                            html.Button("根本をセット", id="btn-set-root"),
                            html.Br(),
                            dcc.Input(id="why-label", placeholder="なぜ？(原因/仮説)", style={"width": 320}),
                            html.Button("選択に追加", id="btn-add-why"),
                            html.Br(),
                            html.Button("選択を削除", id="btn-delete"),
                            html.Span(id="sel-node", style={"marginLeft": 8, "color": "#555"}),
                        ]),
                    ]),
                    html.Div(style={"display": "flex", "gap": 12, "alignItems": "center", "margin": "8px 24px"}, children=[
                        html.Label("レイアウト"),
                        dcc.Dropdown(
                            id="flow-layout",
                            options=[
                                {"label": "横フロー (preset)", "value": "hflow"},
                                {"label": "階層 (breadthfirst)", "value": "breadthfirst"},
                                {"label": "円 (circle)", "value": "circle"},
                                {"label": "グリッド (grid)", "value": "grid"},
                                {"label": "力学 (cose)", "value": "cose"},
                            ],
                            value="hflow",
                            clearable=False,
                            style={"width": 240},
                        ),
                    ]),
                    cyto.Cytoscape(
                        id="flow-chart",
                        elements=[],
                        layout={"name": "preset", "padding": 10},
                        stylesheet=[
                            {"selector": "node", "style": {
                                "content": "data(label)",
                                "shape": "round-rectangle",
                                "text-valign": "center",
                                "text-halign": "center",
                                "text-wrap": "wrap",
                                "text-max-width": 140,
                                "width": "label",
                                "height": "label",
                                "background-color": "#1976d2",
                                "color": "white",
                                "font-size": 14,
                                "padding": "10px",
                            }},
                            {"selector": "edge", "style": {
                                "curve-style": "bezier",
                                "target-arrow-shape": "triangle",
                                "line-color": "#90caf9",
                                "target-arrow-color": "#90caf9",
                                "width": 2,
                            }},
                        ],
                        style={"width": "calc(100vw - 48px)", "height": "70vh", "border": "1px solid #eee", "margin": "12px 24px", "borderRadius": 8, "background": "#fff"},
                    ),
                    html.Div(id="flow-error", style={"color": "crimson", "marginTop": 8}),
                ]),
            ]),
        ],
    )

    @app.callback(Output("amount", "children"), Input("fruit", "value"))
    def show_amount(fruit: str):
        row = df.loc[df["fruit"] == fruit].iloc[0]
        return f"{fruit}: {row['amount']}"

    # --- Flowchart callbacks ---
    def _wrap_label(text: str, limit: int = 8) -> str:
        if not text:
            return ""
        # スペースがあればブラウザ側のwrapに任せる
        if any(ch.isspace() for ch in text):
            return text
        # CJKなどスペースのない文字列は一定幅で改行を挿入
        return "\n".join([text[i : i + limit] for i in range(0, len(text), limit)])

    def _elements_from_store(store):
        nodes = [{"data": {"id": n["id"], "label": _wrap_label(n["label"])}} for n in store.get("nodes", [])]
        edges = [{"data": {"source": e["source"], "target": e["target"]}} for e in store.get("edges", [])]
        return nodes + edges

    @app.callback(
        Output("sel-node", "children"),
        Input("flow-chart", "tapNodeData"),
    )
    def show_selected_node(tap_node):
        if tap_node and tap_node.get("label"):
            return f"選択中: {tap_node['label']}"
        return "選択中: なし"

    @app.callback(
        Output("flow-store", "data"),
        Input("btn-set-root", "n_clicks"),
        Input("btn-add-why", "n_clicks"),
        Input("btn-delete", "n_clicks"),
        State("root-label", "value"),
        State("why-label", "value"),
        State("flow-chart", "tapNodeData"),
        State("flow-chart", "selectedNodeData"),
        State("flow-chart", "selectedEdgeData"),
        State("flow-store", "data"),
        prevent_initial_call=True,
    )
    def edit_flow(n_root, n_add, n_del, root_label, why_label, tap_node, sel_nodes, sel_edges, store):
        store = store or {"seq": 0, "nodes": [], "edges": []}
        trig = (callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None)

        def _add_node(label):
            store["seq"] = int(store.get("seq", 0)) + 1
            nid = f"N{store['seq']}"
            store["nodes"].append({"id": nid, "label": label})
            return nid

        def _find_node_by_label(label):
            for n in store["nodes"]:
                if n["label"] == label:
                    return n
            return None

        def _ensure_root(label):
            if not label:
                return None
            existing = _find_node_by_label(label)
            return existing["id"] if existing else _add_node(label)

        if trig == "btn-set-root":
            _ensure_root((root_label or "").strip())

        elif trig == "btn-add-why":
            parent_id = None
            if tap_node and tap_node.get("id"):
                parent_id = tap_node["id"]
            elif store["nodes"]:
                parent_id = store["nodes"][0]["id"]  # フォールバック: 最初のノード
            if parent_id and (why_label or "").strip():
                child_id = _add_node(why_label.strip())
                store["edges"].append({"source": parent_id, "target": child_id})

        elif trig == "btn-delete":
            # ノード優先で削除
            to_delete_nodes = {n.get("id") for n in (sel_nodes or [])}
            if to_delete_nodes:
                store["nodes"] = [n for n in store["nodes"] if n["id"] not in to_delete_nodes]
                store["edges"] = [e for e in store["edges"] if e["source"] not in to_delete_nodes and e["target"] not in to_delete_nodes]
            else:
                to_delete_edges = {(e.get("source"), e.get("target")) for e in (sel_edges or [])}
                if to_delete_edges:
                    store["edges"] = [e for e in store["edges"] if (e["source"], e["target"]) not in to_delete_edges]

        return store

    @app.callback(
        Output("flow-chart", "elements"),
        Output("flow-chart", "layout"),
        Output("flow-error", "children"),
        Input("flow-store", "data"),
        Input("flow-spec", "value"),
        Input("flow-layout", "value"),
        prevent_initial_call=False,
    )
    def update_flow(store, spec, layout_name):
        try:
            elements = []
            node_ids = []
            edge_pairs = []
            if store and (store.get("nodes") or store.get("edges")):
                elements = _elements_from_store(store)
                node_ids = [n["data"]["id"] for n in elements if "source" not in n.get("data", {})]
                edge_pairs = [(
                    e["data"]["source"], e["data"]["target"]
                ) for e in elements if "source" in e.get("data", {})]
            else:
                nodes = set()
                edges = []
                if spec:
                    for raw in spec.splitlines():
                        line = raw.strip()
                        if not line or line.startswith("#"):
                            continue
                        sep = "->" if "->" in line else ("=>" if "=>" in line else None)
                        if not sep:
                            nodes.add(line)
                            continue
                        left, right = [p.strip() for p in line.split(sep, 1)]
                        if left:
                            nodes.add(left)
                        if right:
                            nodes.add(right)
                        if left and right:
                            edges.append((left, right))
                node_ids = sorted(nodes)
                edge_pairs = edges
                elements = (
                    [{"data": {"id": n, "label": _wrap_label(n)}} for n in node_ids]
                    + [{"data": {"source": s, "target": t}} for s, t in edge_pairs]
                )

            # レイアウト設定
            if layout_name == "hflow":
                # 簡易的な横並び（層ごとにx、同層内はyで整列）
                indeg = {n: 0 for n in node_ids}
                for s, t in edge_pairs:
                    if t in indeg:
                        indeg[t] += 1
                    else:
                        indeg[t] = 1
                    if s not in indeg:
                        indeg[s] = indeg.get(s, 0)
                roots = [n for n, d in indeg.items() if d == 0] or node_ids
                # BFSでレベル付け
                from collections import deque, defaultdict
                level = {n: None for n in node_ids}
                q = deque()
                for r in roots:
                    level[r] = 0
                    q.append(r)
                adj = defaultdict(list)
                for s, t in edge_pairs:
                    adj[s].append(t)
                while q:
                    u = q.popleft()
                    for v in adj.get(u, []):
                        if level.get(v) is None or level[v] < level[u] + 1:
                            level[v] = (level[u] or 0) + 1
                            q.append(v)
                buckets = {}
                for n in node_ids:
                    buckets.setdefault(level.get(n, 0), []).append(n)
                # 座標計算
                xgap, ygap = 240, 120
                new_elements = []
                for data in elements:
                    if "source" in data.get("data", {}):
                        new_elements.append(data)
                for lv, nodes_in_lv in buckets.items():
                    for i, n in enumerate(nodes_in_lv):
                        # ラベルは既存elementsから拾う
                        label = next((d["data"]["label"] for d in elements if d["data"].get("id") == n), n)
                        new_elements.append({
                            "data": {"id": n, "label": label},
                            "position": {"x": lv * xgap + 80, "y": i * ygap + 80},
                        })
                elements = new_elements
                layout = {"name": "preset", "padding": 10}
            else:
                layout = {"name": layout_name, "directed": True, "padding": 10}
            if layout_name == "breadthfirst":
                layout.update({"spacingFactor": 1.1, "animate": False})
            return elements, layout, ""
        except Exception as e:
            return [], {"name": "grid"}, f"Parse error: {e}"

    return app


if __name__ == "__main__":
    # 開発中はデバッグモードが便利です
    create_app().run(debug=True)
