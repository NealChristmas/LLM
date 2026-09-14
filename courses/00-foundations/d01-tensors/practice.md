# D01 配套实验

历史实操资料：当前第一轮不做实验，请读[正文的助记卡片与自测题](README.md)。以下保留供后续深入使用。

先读完[正文](README.md)。实验使用已建立的 CPU 环境，代码见 [experiments.py](code/experiments.py)，版本和实测结果见[验证记录](lab/verification.md)。实验 A、B 共约 50 分钟，包含手算和解释。

## 实验 A：检查数字怎样组织（20 分钟）

运行前写下四种数据的 shape：一个数 7、一组数 [1, 2]、三条各有两个特征的样本、增加第四条样本之后的数据。

在 PowerShell 中执行：

```powershell
Set-Location 'C:\harmonyos-apps\LLM'
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py a
```

将输出与预测对照。脚本打印的 dtype 是元素类型，device 是计算设备；本例统一为 float32 和 CPU。Tensor 的这些属性可在 [PyTorch 官方教程](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)查阅。

重点解释三个区别：轴的数量、每个轴的长度、元素总数。再考虑四条样本各增加一个特征，形状怎样变化。可将结果记入 [D01 学习记录](../../../notes/d01.md)。

## 实验 B：验证权重怎样影响结果（30 分钟）

沿用正文中的 X = [[1,2],[3,4],[5,6]]、W = [[2],[3]]、b = [1]。先手算三条输出，再运行：

```powershell
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py b
```

结果应为 [[9],[19],[29]]。脚本还会比较两种乘法。对下面的矩阵，先计算两种结果的左上角，再查看程序结果：

```text
A = [[1, 2],       C = [[5, 6],
     [3, 4]]            [7, 8]]
```

`A * C` 对应位置相乘，左上角为 5；`A @ C` 将左行与右列对应相乘再求和，左上角为 19。两种结果都为 [2,2]，因此仅检查 shape 不足以证明运算选对了。

输出中的 `EXPECTED_SHAPE_ERROR` 是脚本刻意让 [3,2] 与 [3,1] 相乘，展示不匹配的错误信息。解释为什么缺少一一对应的关系。

然后把第一个权重从 2 改为 4。先写出输出和变化量，再执行：

```powershell
.\.venv\Scripts\python.exe courses/00-foundations/d01-tensors/code/experiments.py b --first-weight 4
```

对照预测并解释：为什么三条输出的变化量不相同？输出变大是否说明模型变好？要回答第二问，还需要什么信息？

## 出现问题时

| 现象 | 检查 |
| --- | --- |
| 找不到 torch | 使用根目录 `.venv` 中的 Python |
| 矩阵形状不匹配 | 输入特征数与权重输入轴是否对应 |
| shape 正确但结果不符 | 是否混用了 `*` 和 `@`，输入及参数是否一致 |
| dtype 不匹配 | 参与矩阵乘法的张量是否均为 float32 |

当前环境已观察到的导入提示及其影响记录在[验证记录](lab/verification.md)。完成实验后做[独立练习](exercises.md)；想进一步看多层计算，可以选读[隐藏层与 ReLU](optional-hidden-layer.md)。
