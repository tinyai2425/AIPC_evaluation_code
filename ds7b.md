# DeepSeek-R1-Distill-Qwen-7B（量化版）

### 1. 模型名称
DeepSeek-R1-Distill-Qwen-7B

### 2. 模型来源
[deepseek-ai/DeepSeek-R1-Distill-Qwen-7B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B)

### 3. 上下文长度（KV Cache）
4K Tokens

### 4. 硬件适配
鸿蒙 PC

### 5. 模型精度
本模型在 **CEval（Chinese Evaluation Benchmark）** 数据集上进行了评测。  
CEval 是一个用于评估中文大语言模型综合能力的测试集，涵盖 52 个学科领域，以多项选择题形式评估模型的知识、推理与语言理解能力。

- **测试题量：** 1346  
- **评测指标：** Accuracy（准确率）  

| 指标 | 浮点模型 | 量化模型 | Recovery |
|------|-----------|-----------|-----------|
| CEval 精度 | 59.55% | 56.84% | 95.44% |
