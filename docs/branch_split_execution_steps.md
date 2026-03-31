# Branch Split Execution Steps

## Purpose

鏈枃妗ｇ敤浜庢妸姝ｅ紡鍒囧嚭 `shared` / `trading` 鍒嗘敮涔嬪墠鐨勬墽琛屽姩浣滄暣鐞嗕负鍙€愭鎺ㄨ繘鐨勬楠ゆ竻鍗曘€?

閲嶇偣涓嶆槸涓€娆℃€у畬鎴愮洰褰曡縼绉伙紝涔熶笉鏄珛鍗抽噸鍐欑幇鏈夌粨鏋勶紝鑰屾槸锛?

- 鍏堝浐瀹氳竟鐣?
- 鍏堝喕缁撴棫璺緞鍥炴祦
- 鍏堝缓绔?shared 涓诲共鍙獙璇佸熀绾?
- 鍐嶅湪绾︽潫鏄庣‘鐨勫墠鎻愪笅鍒囧垎鍒嗘敮

鏈枃妗ｄ腑鐨勬瘡涓€姝ラ兘鎸変互涓嬬粨鏋勭粍缁囷細

- `Goal`
- `Scope`
- `Do First`
- `Do Not Do Yet`
- `Exit Criteria`

## Step 1. Freeze Entry Backflow

### Goal

鍐荤粨鏃у叆鍙ｅ眰缁х画鍚告敹鏂拌兘鍔涚殑瓒嬪娍锛岄伩鍏嶅湪姝ｅ紡鍒囧嚭 `shared` / `trading` 鍒嗘敮涔嬪墠锛屾柊澧炰唬鐮佺户缁洖娴佸埌鏃х殑鍛戒护璺緞銆?

### Scope

- `scripts/commands/`
- `run.py`

### Do First

- 鏄庣‘ `scripts/commands/*.py` 褰撳墠浠呬綔涓哄吋瀹瑰叆鍙ｅ眰淇濈暀銆?
- 鏄庣‘ `run.py` 褰撳墠浠呮壙鎷呯粺涓€鍏ュ彛銆佹敞鍐屻€佸垎鍙戣亴璐ｃ€?
- 绾﹀畾鏂板涓氬姟缂栨帓浼樺厛钀藉埌锛?
  - `pipelines/`
  - `application/shared/`
- 缁欑幇鏈夊懡浠よˉ鍏呭綊灞炶鏄庯細
  - `data`
  - `factor`
  - `ic`
  - `backtest`

### Do Not Do Yet

- 涓嶇珛鍒婚噸鍐?CLI 鑷姩娉ㄥ唽閫昏緫銆?
- 涓嶄竴娆℃€ц縼绉诲叏閮ㄥ懡浠ゆ枃浠躲€?
- 涓嶅湪杩欎竴闃舵鐩存帴寮曞叆鏂扮殑瀹屾暣澶氬叆鍙?CLI 浣撶郴銆?

### Exit Criteria

- 鏂板鑳藉姏涓嶅啀浼樺厛钀藉叆 `scripts/commands/*.py`銆?
- `run.py` 鐨勮亴璐ｈ竟鐣岃鏄庣‘闄愬埗鍦ㄥ叆鍙ｅ垎鍙戝眰銆?
- 鐜版湁鍛戒护鐨?shared / boundary / trading 褰掑睘璇存槑宸插浐瀹氥€?

### Current Progress

Status: complete

宸插畬鎴愶細

- `factor`銆乣ic`銆乣backtest` 鐨勪笟鍔＄紪鎺掑凡浼樺厛涓嬫矇鍒?`pipelines/`锛屽叾涓?`factor` 涓?`ic` 宸茶繘涓€姝ヤ笅娌夊埌 `application/shared/`銆?- `data` 鍛戒护宸茶ˉ榻愪笌 `factor` / `ic` / `backtest` 涓€鑷寸殑 `command -> pipeline -> application` 涓嬫矇妯″紡锛屼笉鍐嶇敱 `scripts/commands/data.py` 鐩存帴鎵挎媴鏃ユ湡鑼冨洿瑙ｆ瀽銆佹壒閲忔洿鏂扮紪鎺掍笌缂撳瓨鐘舵€佺粺璁＄瓑涓氬姟閫昏緫銆?- `run.py` 宸叉槑纭负缁熶竴鍏ュ彛涓庡垎鍙戝眰銆?- 鍏ュ彛灞傝亴璐ｈ鏄庡凡琛ュ厖鍒?`run.py` 涓庣浉鍏冲懡浠ゆ枃浠讹紝褰撳墠 command 灞傜殑鍓╀綑鑱岃矗闄愬畾涓哄弬鏁版敞鍐屻€乸ipeline 璋冪敤涓庣粨鏋滆緭鍑恒€?- 鐜版湁鍥涗釜鍛戒护鐨勫綋鍓嶇姸鎬佸凡鍙槑纭櫥璁颁负锛?  - `data`: 宸蹭笅娌夊埌 pipeline/application
  - `factor`: 钖勫叆鍙?  - `ic`: 钖勫叆鍙?  - `backtest`: 钖勫叆鍙?
缁撹锛?
- Step 1 鐨勪富瑕佹敹鍙ｇ洰鏍囧凡瀹屾垚锛屾棫鍏ュ彛灞傜户缁惛鏀舵柊鑳藉姏鐨勪富瑕佸洖娴佺偣宸茬粡浠?`scripts/commands/` 鏀舵暃鍒?`pipelines/` 涓?`application/shared/`銆?- 褰撳墠闃舵鍙互灏?Step 1 鐘舵€佹洿鏂颁负 `complete`锛屽悗缁嫢鍐嶆柊澧炲懡浠ゆ垨鍏ュ彛鑳藉姏锛屽簲缁х画閬靛畧鈥滃懡浠ゅ眰淇濇寔钖勫叆鍙ｂ€濈殑绾︽潫锛岃€屼笉鏄洖娴佸埌鏃у懡浠ゆ枃浠朵腑銆?
## Step 2. Constrain DataService Boundary

### Goal

鎶?`DataService` 绋冲畾涓?shared data facade锛岃€屼笉鏄户缁啫鑳€涓哄満鏅紪鎺掍腑蹇冦€?

### Scope

- `data/services/data_service.py`

### Do First

- 鍥哄畾 `DataService` 鐨勪笁绫绘帴鍙ｅ垎缁勶細
  - shared raw data access
  - shared analysis input access
  - legacy / boundary warning
- 绾﹀畾鏂板 shared 鏁版嵁鑳藉姏浼樺厛杩涘叆鍓嶄袱绫绘帴鍙ｃ€?
- 鎶婂凡鏈?factor / IC / backtest 鍦烘櫙鍖栨柟娉曡涓哄吋瀹瑰眰锛岃€屼笉鏄湭鏉ユ柊澧炶兘鍔涙壙杞界偣銆?
- 鏄庣‘涓婂眰 application 缂栨帓璐熻矗缁勭粐 lookback / buffer / horizon 绛夊満鏅鍒欍€?

### Do Not Do Yet

- 涓嶆妸 `DataService` 鎵撴暎鍥炵洿鎺ヨ闂?loader / provider銆?
- 涓嶄竴娆℃€у垹闄ゆ棫鎺ュ彛銆?
- 涓嶇户缁悜 `DataService` 澧炲姞 execution / signal / content / trade decision 绛夊己鍦烘櫙鎺ュ彛銆?

### Exit Criteria

- `DataService` 鐨勫叡浜亴璐ｈ绋冲畾闄愬畾銆?- 鏂伴渶姹備笉鍐嶆帹鍔ㄥ畠缁х画鍦烘櫙鑶ㄨ儉銆?- shared 鍒嗘敮鏈潵鍙互鐩存帴鎵挎帴杩欏眰 facade锛岃€屼笉寮曞叆 trading 鍙嶅悜姹℃煋銆?
### Current Progress

Status: complete

宸插畬鎴愶細

- `DataService` 鐨勬帴鍙ｅ凡鎸?shared raw data access銆乻hared analysis input access銆乴egacy / boundary warning 涓夌粍瀹屾垚鍒嗙粍涓庢敞閲娿€?- `factor`銆乣ic` 鐨勪富璺緞宸蹭紭鍏堝湪 application 灞傜粍缁囧満鏅鍒欙紝鍐嶈皟鐢ㄥ叡浜垎鏋愯緭鍏ユ帴鍙ｃ€?- `backtest` 涓昏矾寰勫凡浠?`get_analysis_backtest_panel(...)` 鍒囧洖閫氱敤鐨?`get_analysis_panel(...)`锛宔xecution delay / buffer 瑙勫垯涓嶅啀缁х画浣滀负 `DataService` 鐨勪富鎺ㄨ崘鑱岃矗銆?- `docs/data_service_boundary.md` 宸插悓姝ヨ褰曞綋鍓嶅叡浜竟鐣屻€佸吋瀹规帴鍙ｄ笌鏀跺彛鍘熷垯銆?- `DataService` 涓殑鏃у満鏅寲鎺ュ彛涓庢棫鍒悕鎺ュ彛宸茬粡琛ュ厖 `DeprecationWarning`锛岄€€鍦虹瓥鐣ヤ粠绾敞閲婄害鏉熸帹杩涘埌杩愯鏃舵彁绀恒€?- 宸插畬鎴愪竴杞皟鐢ㄧ偣娓呯偣锛岀‘璁?factor / ic / backtest 涓昏矾寰勯兘涓嶅啀渚濊禆 `get_analysis_factor_panel(...)`銆乣get_analysis_backtest_panel(...)`銆乣get_analysis_ic_panel(...)` 鍙婂搴旀棫鍒悕鏉ョ粍缁囧満鏅鍒欍€?
缁撹锛?
- Step 2 鐨勪富鏀跺彛鐩爣宸茬粡瀹屾垚锛宍DataService` 浣滀负 shared data facade 鐨勮竟鐣屻€佷富璺緞涓庡吋瀹瑰眰閫€鍦虹瓥鐣ラ兘宸插浐瀹氥€?- 褰撳墠闃舵鍙互灏?Step 2 鐘舵€佹洿鏂颁负 `complete`锛涘悗缁嵆浣挎棫鎺ュ彛鍥犲吋瀹规€ф殏鏃朵繚鐣欙紝涔熶笉鍐嶅奖鍝?Step 2 瀵光€滀富璺緞宸插畬鎴愭敹鍙ｂ€濈殑鍒ゆ柇銆?
## Step 3. Clarify Backtest Ownership

### Goal

鏄庣‘ `backtest/` 涓摢浜涜兘鍔涘睘浜?shared analysis锛屽摢浜涜兘鍔涘睘浜?trading/runtime 璇箟锛岄伩鍏嶅垏鍒嗘椂鏁村潡鐩綍褰掑睘澶辨帶銆?

### Scope

- `backtest/`

### Do First

- 鐩樼偣 `backtest/` 鍐呯幇鏈夎兘鍔涘苟鍒嗕负涓夌被锛?
  - shared analysis capability
  - boundary-controlled capability
  - trading/runtime-specific capability
- 鏄庣‘鍝簺缁撴灉瀵硅薄銆佸垎鏋愭祦绋嬨€佺粺璁″彛寰勫彲琚?shared 澶嶇敤銆?
- 鏄庣‘鍝簺鎵ц銆佽皟浠撱€佹垚鏈€佹寔浠撱€佸欢杩熻涔夋洿閫傚悎涓嬫矇 trading銆?
- 琛ヤ竴浠?`backtest` owned vs boundary 璇存槑銆?

### Do Not Do Yet

- 涓嶆妸鏁翠釜 `backtest/` 鐩存帴鏁翠綋鍒掑綊 `shared` 鎴?`trading`銆?
- 涓嶅湪杈圭晫鏈竻鏅板墠鍋氬ぇ瑙勬ā鐩綍杩佺Щ銆?
- 涓嶆妸鎵€鏈?simulation / execution 缁嗚妭閮芥壙璇轰负 shared 鑳藉姏銆?

### Exit Criteria

- `backtest/` 鐨?shared / boundary / trading 杈圭晫璇存槑娓呮櫚銆?- 鑷冲皯鑳借娓呮锛?  - 鍝簺鑳藉姏淇濈暀 boundary-controlled
  - 鍝簺鏈潵涓嬫矇 trading
  - 鍝簺鍙互鎶藉埌 shared
- 鍚庣画鍒囧垎鍒嗘敮鏃讹紝`backtest/` 涓嶄細缁х画鏃犺竟鐣屾墿寮犮€?
### Current Progress

Status: complete

宸插畬鎴愶細

- 宸茶ˉ鍏?`docs/backtest_ownership.md`锛屽 `backtest/` 褰撳墠鐨?ownership 鍋氫簡绗竴鐗堟寮忚鏄庛€?- 褰撳墠宸叉槑纭?`backtest/` 鏁翠綋浠嶄繚鎸佷负 `boundary-controlled`锛屼笉鐩存帴鏁翠綋鍒掑綊 `shared` 鎴?`trading`銆?- 宸插畬鎴愪竴杞寜鏂囦欢鐨勫垵姝ュ垎绫伙細
  - `backtest/analysis/result_analyzer.py` 浣滀负 shared analysis capability 鍊欓€?  - `backtest/simulation/execution_model.py` 涓?`backtest/simulation/portfolio_manager.py` 浣滀负 trading/runtime-specific 鍊欓€?  - `backtest/engine/backtest_engine.py`銆乣backtest/simulation/signal_generator.py`銆乣backtest/simulation/pnl_calculator.py` 褰撳墠淇濈暀涓?boundary-controlled 缁勪欢
- 宸茶繘涓€姝ョ粏鍖?`engine / simulation / results` 涓夊眰杈圭晫锛屽苟鏄庣‘ `backtest/results/runs/` 鍚庣画鏇存帴杩戝榻?`storage/trading_system/backtests/`銆?- 宸茬粰鍑烘湭鏉ヨ縼绉讳紭鍏堢骇锛屾槑纭摢浜涚粍浠朵紭鍏堣縼寰€ trading/runtime锛屽摢浜涙洿鍙兘缁х画娌夋穩涓?shared analysis锛屽摢浜涚户缁繚鐣欎负 boundary-controlled銆?
缁撹锛?
- Step 3 鐨?ownership 璇存槑宸茬粡浠庡垵姝ュ垎绫绘帹杩涘埌鏇寸ǔ瀹氱殑杈圭晫瑙勫垯涓庤縼绉讳紭鍏堢骇鍒ゆ柇銆?- 褰撳墠闃舵鍙互灏?Step 3 鐘舵€佹洿鏂颁负 `complete`锛屽悗缁嫢缁х画璋冩暣 backtest 浠ｇ爜鎴栫粨鏋滆矾寰勶紝搴旈伒瀹堝綋鍓嶆枃妗ｄ腑宸茬粡鍥哄畾鐨?ownership 涓庤縼绉绘柟鍚戯紝鑰屼笉鏄噸鏂板洖鍒版暣鍧楃洰褰曞綊灞炰笉娓呯殑鐘舵€併€?
## Step 4. Clarify Research Asset Ownership

### Goal

明确 `models/alpha/` 与 `strategies/` 的共享资产边界，避免研究实现、产品逻辑和交易运行时语义混在一起。

### Scope

- `models/alpha/`
- `strategies/`

### Do First

- 定义共享研究资产与分支私有资产的判断标准。
- 盘点 `models/alpha/`：
  - 哪些是共享最小协议或轻量 alpha 能力
  - 哪些已经带产品化或特定业务语义
- 盘点 `strategies/`：
  - 哪些只是研究样例
  - 哪些已明显偏向交易运行或实盘语义
- 先补文档归属说明，不急于移动文件。

### Do Not Do Yet

- 不批量迁移 `models/alpha/` 或 `strategies/`。
- 不把所有 alpha / strategy 默认视为 shared 资产。
- 不把实验性实现过早冻结成 shared 契约。

### Exit Criteria

- `models/alpha/` 与 `strategies/` 的 owned vs boundary 规则明确。
- 已能区分：
  - 共享最小协议
  - 研究实现资产
  - trading/runtime 相关资产
- 分支切出后，不会因为归属不明产生频繁双向复制或反复迁移。

### Current Progress

Status: in progress

已完成：

- 已补充 `docs/research_asset_ownership.md`，形成 research asset ownership 初稿。
- `models/alpha/` 当前已明确更接近 `shared minimal alpha capability`。
- `strategies/` 当前已明确更接近 `research implementation assets`。
- 当前这部分 ownership 判断已经落文档，但后续仍需继续补强新增资产的落点规则。

结论：

- Step 4 已从空白阶段推进到“ownership 初稿已固定”的状态。
- 但当前更准确的阶段仍应记为 `in progress`；后续还需要把初稿分类提升为可持续复用的新增资产判断标准。

## Step 5. Stabilize Shared Smoke Baseline

### Goal

在切出 `shared` 分支前，先建立最小可运行的 shared regression baseline，确保后续 shared 主干有稳定的基础回归入口。

### Scope

- `tests/data`
- `tests/pipelines`
- `tests/utils`
- `tests/backtest`
- `docs/shared_test_strategy.md`

### Do First

- 固定 shared smoke suite 的最小范围。
- 优先覆盖以下路径：
  - shared data load path
  - panel / universe 基础稳定性
  - factor pipeline 主链
  - IC pipeline 主链
  - metadata / run tracker / exceptions
  - shared backtest analysis loop
- 尽量保证这套测试：
  - 执行快
  - 依赖少
  - 不强依赖本地缓存状态
  - 失败后易定位

### Do Not Do Yet

- 不追求一次性补齐高覆盖率。
- 不把 execution / portfolio / risk / strategy-specific 测试混入 shared suite。
- 不引入过重、过慢、强依赖本地数据状态的测试集合。

### Exit Criteria

- shared 分支具备最小可运行回归基线。
- shared 改动可被快速验证。
- trading 分支可以在 shared baseline 之上独立扩展自身测试。

### Current Progress

Status: complete

已完成：

- 已补充 `docs/shared_test_strategy.md`，把当前 shared regression 的边界、范围与 smoke suite 目标写清楚。
- 已将 shared smoke baseline 固定为一组可直接执行的最小测试集合，当前纳入的 smoke suite 包括：
  - `tests/data/test_analysis_cache.py`
  - `tests/data/test_data_app.py`
  - `tests/data/test_loaders.py`
  - `tests/data/test_processing.py`
  - `tests/pipelines/test_data_pipeline.py`
  - `tests/pipelines/test_factor_pipeline.py`
  - `tests/pipelines/test_ic_pipeline.py`
  - `tests/utils/test_result_metadata.py`
  - `tests/utils/test_run_tracker.py`
  - `tests/backtest/test_backtest_engine.py`
- 当前这组 baseline 已能覆盖 shared data/cache path、loader / processing 最小有效链路、factor / ic / data pipeline 轻量主链、metadata / run tracker 与 shared backtest analysis loop。
- `docs/shared_test_strategy.md` 已固定统一的 pytest 执行入口，可直接作为 shared smoke suite 的最小执行命令。

结论：

- Step 5 的 shared smoke baseline 已从“初稿”推进为“固定测试集合 + 明确执行入口”的完成态。
- 当前阶段可以将 Step 5 状态更新为 `complete`；后续若继续扩展 shared regression scope，应在这套 smoke baseline 之上增量推进，而不再回到 baseline 未固定的状态。

## Step 6. Final Pre-Split Review

### Goal

鍦ㄦ寮忓垏 `shared` / `trading` 鍒嗘敮鍓嶏紝瀵瑰墠 5 姝ョ殑杈圭晫绾︽潫鍋氫竴娆＄粺涓€纭锛岄伩鍏嶅甫鐫€鏈敹鍙ｇ殑闂鐩存帴鍒囧垎銆?

### Scope

- entry layer
- DataService boundary
- backtest ownership
- research asset ownership
- shared smoke baseline

### Do First

- 閫愰」纭 Step 1 鍒?Step 5 鐨?exit criteria 鏄惁婊¤冻銆?
- 纭鏂板浠ｇ爜钀界偣瑙勫垯宸茬粡瀹為檯鐢熸晥銆?
- 纭 shared / boundary / trading 鐨勫垎绫讳笉鍐嶅仠鐣欏湪鍙ｅご绾﹀畾銆?
- 纭 shared smoke baseline 宸插彲绋冲畾浣滀负鍒囧垎鍚庨獙璇佸熀纭€銆?

### Do Not Do Yet

- 涓嶅湪 exit criteria 鏈弧瓒虫椂浠撲績鍒囧垎鏀€?
- 涓嶆妸鈥滃凡鏈夌洰褰曢鏋垛€濊鍒や负鈥滃凡缁忓畬鎴愯竟鐣屾敹鍙ｂ€濄€?

### Exit Criteria

- Step 1 鍒?Step 5 宸插熀鏈畬鎴愩€?
- 鍙互鍦ㄤ笉澶ц妯￠噸鍐欍€佷笉涓€娆℃€ф惉绌虹洰褰曠殑鍓嶆彁涓嬫寮忓垏鍑?`shared` / `trading` 鍒嗘敮銆?
- 鍒囧垎涔嬪悗涓ゆ潯鍒嗘敮閮借兘鍦ㄦ槑纭竟鐣屼笅缁х画婕旇繘銆?

## Split Readiness Gate

褰撲互涓嬫潯浠跺叏閮ㄦ弧瓒虫椂锛屽彲浠ヨ涓轰粨搴撳凡缁忚揪鍒版寮忓垏 `shared` / `trading` 鍒嗘敮鐨勬渶浣庨棬妲涳細

- 鏂颁唬鐮佷笉鍐嶅洖娴佹棫鍛戒护灞傘€?
- `DataService` 涓嶅啀缁х画鍦烘櫙鑶ㄨ儉銆?
- `backtest/` 鐨?shared / boundary / trading 杈圭晫宸插啓娓呮銆?
- `models/alpha/` 涓?`strategies/` 鐨勫綊灞炲師鍒欏凡鍐欐竻妤氥€?
- shared smoke suite 鍙互绋冲畾鎵ц銆?


