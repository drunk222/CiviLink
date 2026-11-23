# 万象同纹 · 馆藏中的文明对话

ChinaVis 2024「数智互鉴」赛题实践，本地数字人文可视分析工作台，版本0.4。

## 启动

需要Node.js 18或以上，无前端第三方依赖，无需npm install。

首次从GitHub获取（图片较多，请等待克隆完成）：

```powershell
git clone https://github.com/drunk222/CiviLink.git
cd CiviLink
npm start
```

已有本地项目时：

```powershell
cd D:\CiviLink
npm start
```

打开 http://127.0.0.1:5173/#explore 。终端保持运行，Ctrl+C停止。不要直接双击index.html：数据通过本地HTTP读取。端口占用时先设置 `$env:PORT=5174`。

## 核心可视化

- 万象星图：4312点对应4312条记录；材料星群/时间织图切换，机构着色，点选详情。
- 年代叠流：按世纪中点归箱，堆叠显示机构贡献；世纪条点选和双滑块年代筛选。
- 藏品年轮：机构→主材料的双环旭日图，可逐层下钻，配精确条图。
- 器物经纬：机构→主材料→主工艺三列流带，数量守恒，点击节点筛选。
- 同纹异藏：纹样候选×机构气泡矩阵，可切换记录数/机构内占比，点击单元格下钻。

统一筛选联动所有视图；24条/页浏览全部记录。保留详情、完整原始字段、2—4条对照、策展保存、CSV/JSON导出与URL分享。

详细设计、编码与解释边界见 [可视化组件设计](docs/可视化组件设计.md)。

## 全集数据与边界

全部4312条官方元数据已接入，主键cv-Main_ID；保留8种原始机构标签。4312指记录数，不是去重实物数。同机构同馆藏编号存在329条超出首条的重复记录，可能是多图或重复条目，当前不擅自合并。

202条数值年代与严格原文年段存在冲突，已按原文明确的公元年段规范化；rawStart/rawEnd保留原数值。另有50条公元前文本记录按原文修正：18条区间符号或端点冲突（含2条整段落入公元）、32条单世纪展开为约100年区间，rawStart/rawEnd保留原值。11条原始缺失与1条复杂冲突保留为待定，因此4300条可进入年代图。所有记录均可通过默认筛选访问。详情展示处理依据。

792条记录有文字纹样候选：规则仅使用名称和Metadata，不使用AAT噪声词表、不从图像推断；英文词加边界以避免dragonfly、thunderbird等误配。候选未经人工图像确认，不证明传播关系。主材料和工艺按明确词汇分组；原字段缺失时，从原名称、分类或已核查描述中补全432条材料和92条工艺，均保留字段出处与category/title/editorial依据类型。另提供materialAll/techniqueAll多标签和同馆藏号重复标记（duplicateGroupSize/duplicateIndex），但图表主类仍按原口径，重复行不删除。补全后材料仍缺606条、技法仍缺1269条，展示为“资料未提供”。P4的258与259已按馆方描述补为玉斧、玉琮及玉材质，工艺不猜测。规则在scripts/import_official.py中公开；原文保留。

完整官方包已下载，大小1,288,822,982字节；实际包内4312张JPG全部提取并通过原RAR条目的CRC32校验，4312条记录均已关联图片，未匹配、歧义匹配及损坏均为0。原图保留在assets/official/images，180px缩略图和1600px详情图按需加载。原先10件The Met研究案例和9张公共领域图片独立保留，不加入官方统计。

## 数据与维护

- data/official-records.json：4312条原始表记录。
- data/official-collection.json：前端统一模型，原表行号和rawIndex可追溯。
- data/normalized-audit.json：本版清洗审计。
- data/official/：已校验的原始XLSX。
- data/collection.json：独立The Met案例。
- lib.js、viz-lib.js：筛选与聚合纯函数。
- charts.js：Canvas/SVG绘图；app.js：页面状态与交互。

```powershell
npm test
npm run data:normalize
```

重新生成官方前端模型只需Python标准库，无需联网或修改XLSX。原始表来自 https://chinavis.org/2024/document/channel2_data.rar ，获取与校验过程见docs/官方数据获取.md。

清洗与可视化自动检查、图片完整性及浏览器检查见 [0.4清洗修订记录](docs/验证记录-v4.md) 与 [0.3验证记录](docs/验证记录-v3.md)。

## 悬停与响应优化

图表统一使用即时提示卡片，浏览器原生SVG title已移除。星图使用缓存底图、空间索引命中及每帧合并指针事件，移动时只更新高亮；不重复绘制4312点。图片使用180px缩略图、懒加载和长期缓存；原始字段按单记录data/records/cv-ID.json加载。文字主题的提取方式集中到详情和方法说明，提示卡不再反复显示技术限定语。

图片重建需要包含Pillow的Python：先运行scripts/safe_image_archive.py（完整RAR转安全文件名归档），用tar解压到assets/official，再运行scripts/build_images.py和scripts/import_official.py。当前交付已包含全部原图、派生图和关联索引，日常npm start不需要Python或联网。

## 仓库中的资源

仓库包含完整元数据、4312张原图、缩略图和详情图。约1.29GB的下载用RAR、分段文件和临时缓存不提交；重建时可按上文官方来源重新下载。图片与馆藏资料的权利归原机构或权利人，字段中的来源及版权信息予以保留，本项目不另行授予这些资源的使用许可。
