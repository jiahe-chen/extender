# Top-2策略数据分析（重点：diff_eval）

数据范围：qwen3-8b，240样本；Top-2策略=run_1；Top-1策略=run_2；workflow=single_agent/two_agent/diff_eval。

## 关键结论（diff_eval优先）
- diff_eval：run_2 Top-1 Acc=61.25%；run_1 Hit@2=83.75%；绝对提升=+22.50%
- diff_eval：MRR@2=0.7208；Top-2的“Pos2-only贡献”=23.33%（Top-1错但Top-2命中）
- diff_eval：GT在all_checks“被检测到(任意位置)”的比例=92.50%；但未进入Top-2的比例=8.75%（Top-2排序/裁剪损失）
- run_1横向对比：Hit@2最高的是diff_eval=83.75%；但diff_eval的平均耗时=150.6s/样本（single/two agent为秒级）
- 备注：按你的要求在图中标注随机baseline：Top-1=25%，Top-2=40%。（Top-2=2/5=40%与5类标签一致；Top-1=25%对应4类假设，若按5类则应为20%。）

## Top-2相对Top-1的提升（run_1 Hit@2 vs run_2 Top-1）
```text
    workflow  run_2_top1_acc  run_1_hit@2  abs_delta
single_agent          0.3000       0.6458     0.3458
   two_agent          0.4417       0.6417     0.2000
   diff_eval          0.6125       0.8375     0.2250
```

## Overall Performance（各workflow）
```text
    strategy   run   n  top1_acc  top2_acc  mrr@2  macro_f1_top1  micro_f1_top1  macro_f1_top2_resolved  micro_f1_top2_resolved  set_f1@2  pos2_only_share  mean_time_s  median_time_s  mean_loc
   diff_eval run_1 240    0.6042    0.8375 0.7208         0.6072         0.6042                  0.8439                  0.8375    0.5611           0.2333     150.6492       129.1400  159.7958
single_agent run_1 240    0.3625    0.6458 0.5042         0.2977         0.3625                  0.6477                  0.6458    0.4306           0.2833       3.1447         3.0400  159.7958
   two_agent run_1 240    0.4333    0.6417 0.5375         0.3893         0.4333                  0.6299                  0.6417    0.4417           0.2083       7.1145         5.3500  159.7958
   diff_eval run_2 240    0.6125    0.6125 0.6125         0.6120         0.6125                  0.6120                  0.6125    0.6125           0.0000     151.5840       124.9150  159.7958
single_agent run_2 240    0.3000    0.3000 0.3000         0.2210         0.3000                  0.2210                  0.3000    0.3000           0.0000       2.0567         1.9350  159.7958
   two_agent run_2 240    0.4417    0.4417 0.4417         0.4270         0.4417                  0.4270                  0.4417    0.4417           0.0000       3.4696         2.6750  159.7958
```

## 按难度（EASY/MODERATE/HARD）
```text
    strategy   run    level  n  top1_acc  top2_acc  mrr@2  macro_f1_top1  macro_f1_top2_resolved  set_f1@2  pos2_only_share  mean_loc
   diff_eval run_1     EASY 80    0.6875    0.8500 0.7688         0.6881                  0.8480    0.5750           0.1625   33.1750
   diff_eval run_1     HARD 80    0.6125    0.8000 0.7063         0.6210                  0.8180    0.5333           0.1875  305.7875
   diff_eval run_1 MODERATE 80    0.5125    0.8625 0.6875         0.4976                  0.8584    0.5750           0.3500  140.4250
single_agent run_1     EASY 80    0.5500    0.9125 0.7312         0.4474                  0.9109    0.6083           0.3625   33.1750
single_agent run_1     HARD 80    0.2375    0.4375 0.3375         0.1320                  0.3511    0.2917           0.2000  305.7875
single_agent run_1 MODERATE 80    0.3000    0.5875 0.4437         0.2327                  0.5737    0.3917           0.2875  140.4250
   two_agent run_1     EASY 80    0.5875    0.8125 0.7000         0.5642                  0.7887    0.5750           0.2250   33.1750
   two_agent run_1     HARD 80    0.3125    0.4875 0.4000         0.2361                  0.4642    0.3250           0.1750  305.7875
   two_agent run_1 MODERATE 80    0.4000    0.6250 0.5125         0.3234                  0.6035    0.4250           0.2250  140.4250
   diff_eval run_2     EASY 80    0.6750    0.6750 0.6750         0.6746                  0.6746    0.6750           0.0000   33.1750
   diff_eval run_2     HARD 80    0.6125    0.6125 0.6125         0.6168                  0.6168    0.6125           0.0000  305.7875
   diff_eval run_2 MODERATE 80    0.5500    0.5500 0.5500         0.5353                  0.5353    0.5500           0.0000  140.4250
single_agent run_2     EASY 80    0.4500    0.4500 0.4500         0.3547                  0.3547    0.4500           0.0000   33.1750
single_agent run_2     HARD 80    0.2000    0.2000 0.2000         0.0667                  0.0667    0.2000           0.0000  305.7875
single_agent run_2 MODERATE 80    0.2500    0.2500 0.2500         0.1563                  0.1563    0.2500           0.0000  140.4250
   two_agent run_2     EASY 80    0.6750    0.6750 0.6750         0.6738                  0.6738    0.6750           0.0000   33.1750
   two_agent run_2     HARD 80    0.2000    0.2000 0.2000         0.0882                  0.0882    0.2000           0.0000  305.7875
   two_agent run_2 MODERATE 80    0.4500    0.4500 0.4500         0.3898                  0.3898    0.4500           0.0000  140.4250
```

## 按Violation类型（SRP/OCP/LSP/ISP/DIP）
```text
    strategy   run violation  n  top1_acc  top2_acc  mrr@2  pos2_only_share
   diff_eval run_1       DIP 48    0.8125    0.9583 0.8854           0.1458
   diff_eval run_1       ISP 48    0.6250    0.9375 0.7812           0.3125
   diff_eval run_1       LSP 48    0.7500    0.7708 0.7604           0.0208
   diff_eval run_1       OCP 48    0.3750    0.7083 0.5417           0.3333
   diff_eval run_1       SRP 48    0.4583    0.8125 0.6354           0.3542
single_agent run_1       DIP 48    0.0000    0.5000 0.2500           0.5000
single_agent run_1       ISP 48    0.0208    0.3125 0.1667           0.2917
single_agent run_1       LSP 48    0.3333    0.4167 0.3750           0.0833
single_agent run_1       OCP 48    0.4583    1.0000 0.7292           0.5417
single_agent run_1       SRP 48    1.0000    1.0000 1.0000           0.0000
   two_agent run_1       DIP 48    0.1875    0.6875 0.4375           0.5000
   two_agent run_1       ISP 48    0.1458    0.4583 0.3021           0.3125
   two_agent run_1       LSP 48    0.1250    0.1667 0.1458           0.0417
   two_agent run_1       OCP 48    0.7500    0.9375 0.8438           0.1875
   two_agent run_1       SRP 48    0.9583    0.9583 0.9583           0.0000
   diff_eval run_2       DIP 48    0.8333    0.8333 0.8333           0.0000
   diff_eval run_2       ISP 48    0.6667    0.6667 0.6667           0.0000
   diff_eval run_2       LSP 48    0.7500    0.7500 0.7500           0.0000
   diff_eval run_2       OCP 48    0.3542    0.3542 0.3542           0.0000
   diff_eval run_2       SRP 48    0.4583    0.4583 0.4583           0.0000
single_agent run_2       DIP 48    0.0000    0.0000 0.0000           0.0000
single_agent run_2       ISP 48    0.0000    0.0000 0.0000           0.0000
single_agent run_2       LSP 48    0.3125    0.3125 0.3125           0.0000
single_agent run_2       OCP 48    0.1875    0.1875 0.1875           0.0000
single_agent run_2       SRP 48    1.0000    1.0000 1.0000           0.0000
   two_agent run_2       DIP 48    0.1042    0.1042 0.1042           0.0000
   two_agent run_2       ISP 48    0.4375    0.4375 0.4375           0.0000
   two_agent run_2       LSP 48    0.1667    0.1667 0.1667           0.0000
   two_agent run_2       OCP 48    0.5208    0.5208 0.5208           0.0000
   two_agent run_2       SRP 48    0.9792    0.9792 0.9792           0.0000
```

## Confusion Matrix（重点diff_eval）
- 图：`05_confusion_matrices_diff_eval.png` 左=run_2 Top-1；右=run_1 Top-2 resolved/Hit@2（用于体现Top-2可覆盖的错误）

## Confusion Matrix（全部workflow）
- 图：`07_confusion_matrices_all_workflows.png` 上排=run_2 Top-1；下排=run_1 Top-2 resolved/Hit@2

## 代码难度/长度：Top-2在长代码上的收益（diff_eval）
- 图：`04_diff_eval_accuracy_by_loc.png`（按LOC四分位）
- 直觉：长输入更容易出现“多个violations并存/边界模糊”，Top-2能减少把次优候选挤到Top-1之外带来的误判。

## 关键案例：长代码多violations（用于justify Top-2）
- `OCP_6` (HARD, 269 LOC): `pred1=DIP` / `pred2=OCP` / `actual=OCP`；Top-1错误但Top-2命中（Pos2-only=True）。

## Literature（Top-1）对齐对比
- 文献overall(top1): 38.44%
- 文献 codellama70b (top1): 15.00%
- 文献 deepseek33b (top1): 15.83%
- 文献 gpt-4o-mini (top1): 69.17%
- 文献 qwen2.5-coder32b (top1): 53.75%
- 图：`06_literature_vs_ours_top1.png`（注意：文献数据集与本项目数据集不完全一致，这里主要用于量级对齐/参考）

## 生成的图表/文件
- `01_overall_accuracy_top1_top2.png`
- `02_diff_eval_rank_distribution.png`
- `03_accuracy_by_difficulty.png`
- `04_diff_eval_accuracy_by_loc.png`
- `05_confusion_matrices_diff_eval.png`
- `06_literature_vs_ours_top1.png`
- `07_confusion_matrices_all_workflows.png`
- `overall_metrics.csv`, `by_difficulty.csv`, `by_violation.csv`
