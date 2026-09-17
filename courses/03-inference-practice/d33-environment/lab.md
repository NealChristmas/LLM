# D33 环境盘点任务

本任务只读取环境，不安装软件、不启动云资源。目标是用证据选择后续实验路线，而不是把所有检查项都变成“通过”。

## 1. 重新采集本机信息

在仓库根目录的 PowerShell 中执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\courses\03-inference-practice\d33-environment\scripts\collect-environment.ps1
```

脚本只调用系统查询命令并输出到终端，不会写注册表、安装驱动或启动服务。将输出与[本次环境报告](records/environment-report.md)比较；若硬件或软件状态发生变化，以新结果为准并记录日期。

## 2. 填写路线决策

复制以下字段到新的个人实验记录中填写，不覆盖现有检测报告：

```text
检查日期：
本机 GPU 与显存：
nvidia-smi 是否可用：
Linux 环境：
Docker Client/Server 状态：
可用磁盘空间：
后续路线（本机 / WSL / 云端）：
目标 GPU 与显存：
选择依据：
尚未确认的风险：
```

## 3. 验收

任务完成时应能给出一段简短结论，明确“哪里执行 GPU 推理”和“为什么”。不要把尚未租用的云 GPU 写成已经可用，也不要把脚本检测结果等同于模型运行成功。
