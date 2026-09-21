# LCC s03 考点与自测

## 一、知识点 / 考点

1. 动机：s02 的 bash 不受限，"清理项目"可能 `rm -rf /`。安全不能靠信任模型，要代码在工具执行前判断。
2. 核心变更：s02 循环保留；工具执行前插入 `check_permission()`。
3. 三道闸门（顺序固定）：① 拒绝列表（硬拒绝：`rm -rf /`、`sudo` 等，命中直接拒绝）② 规则匹配（上下文相关：读写工作区外、`rm` 文件等）命中后交给闸门3 ③ 用户审批（暂停问 y/N）。三道都没命中 → 直接执行。
4. 设计要点：硬拒绝优先（最危险先拦）、软询问次之、默认放行（大部分日常操作走这条）。
5. 闸门1 局限：简单字符串匹配不可靠（命令变体、shell 展开可绕过）→ CC 用 8 个规则来源 + 多阶段管线。
6. CC 对比（进阶）：`PermissionResult` 实为 4 种（allow/deny/ask/**passthrough**，教学版无 passthrough）；验证多阶段；规则来自 8 个来源（user/project/local/flag/policy/cliArg/command/session），高优先级覆盖低；`isDestructive` 纯 UI 展示不参与决策；`YoloClassifier` auto 模式用分类器 LLM 自动审批；子 Agent `permissionMode='bubble'` 权限冒泡到父终端。

## 二、自测题

1. （动机）为什么"安全不能靠信任模型"？s03 在哪个位置加判断？
2. （流程）三道闸门的顺序是什么？为什么是这个顺序？
3. （细节）闸门2 命中后怎样？三道都没命中呢？
4. （局限）闸门1 的字符串匹配有什么问题？举一种绕过方式。
5. （CC对比）CC 的 PermissionResult 有 4 种，教学版缺哪个？它什么意思？
6. （CC对比）CC 的 `isDestructive` 参与权限决策吗？

完成后查看[参考答案](answers/lcc-s03.md)。


