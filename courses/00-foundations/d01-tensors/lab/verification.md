# D01 环境与验证记录

验证日期：2026-09-14。状态：本机 CPU 实验已运行通过；这不是用户的学习完成记录。

正文 2.0 修订说明：重写概念引入顺序，将实验说明与时间安排迁至 practice.md 和 study-guide.md。代码、数据和答案未改动，沿用以下既有运行证据；本次文档修订不声称重新运行实验。

## 环境

- Windows，PowerShell；Python 3.12.14，PyTorch 2.14.0+cpu，float32。
- 独立环境：C:\harmonyos-apps\LLM\.venv。
- 基础解释器：本机 Codex 捆绑的 Python 3.12.14（公开版本隐去包含个人用户名的绝对路径）。
- 无 GPU 操作、无训练、无随机初始化或采样。所有数据是脚本内固定小整数。
- 安装由官方 CPU wheel 索引完成；依赖版本来自实际 pip freeze，见 [requirements.txt](requirements.txt)。

## 已执行的命令

工作目录：C:\harmonyos-apps\LLM。首次建立环境使用上述基础解释器执行 `-m venv .venv`，随后使用新环境安装 torch。

```powershell
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py a
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py b
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py c
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py verify
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py b --first-weight 4
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze
```

各实验与安装命令成功退出，pip check 输出 `No broken requirements found.`。本次无需重新安装；以后重建时在新虚拟环境中执行：

```powershell
python -m pip install -r courses/00-foundations/d01-tensors/lab/requirements.txt
```

这里的 python 须为目标虚拟环境解释器；不是要求在系统环境安装。未在另一台机器验证重建，版本锁定不等于跨平台保证。

## 实测结果摘录

| 检查 | 实测结果 |
| --- | --- |
| A：四种形状 | []、[2]、[3,2]、[4,2]；均为 float32、CPU |
| B：基线 Y | [[9.0],[19.0],[29.0]] |
| B：参数个数 | 3 |
| B：重复前向 | forward_repeated_same_result: True |
| B：逐元素乘法 | [[5.0,12.0],[21.0,32.0]] |
| B：矩阵乘法 | [[19.0,22.0],[43.0,50.0]] |
| B：错误路径 | EXPECTED_SHAPE_ERROR: mat1 and mat2 shapes cannot be multiplied (3x2 and 3x1) |
| B：第一个权重改为 4 | [[11.0],[25.0],[39.0]] |
| C：隐藏层输出 | [[3.0,0.0,0.0],[7.0,0.0,2.0],[11.0,0.0,4.0]] |
| C：最终输出 | [[4.0],[6.0],[8.0]] |
| verify | 前向数值、改参差值、参数未被前向修改、批次一致性、E2/E3答案数值及错误路径断言通过 |

以上是实际执行后的摘录，不是完整原始日志。验证入口属于制作者核对，可能暴露练习数值；学习时优先使用 a、b，完成后再查看 verify。

## 已观察到的环境提示

导入 torch 时提示缺少 NumPy；本课不使用 NumPy 转换，所有实验仍成功完成。还出现“Microsoft Visual C++ Redistributable is not installed”的提示，但本机没有发生 DLL 加载失败。此处只记录库发出的提示，不据此断言系统安装状态；未进行系统运行库安装或修改。

用户若看到这些提示而后续数值正常，可以继续本课；若确实发生导入失败，则按实际错误诊断。验证范围仅为本课 Windows CPU 小规模计算，不包含 GPU、训练或性能评估。

## 制作检查

- 学习目标 G1～G4 与 E1～E5 对应，含解释、计算、错误诊断与变式实验。
- 正文给出术语、形状、单位约定和手算例子，省略通用编程教学。
- 练习与答案分离，学习记录保持待填写。
- 基础与选学范围明确，必学时间合计 240 分钟。
- 原理来源已列入正文，数学结果经手算与运行核对；本地链接交付时检查。
- 版本 1.0；未声称学习者已通过验收。
