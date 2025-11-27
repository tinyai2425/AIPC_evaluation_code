import json
def quant_config_set(file_path, save_path, lora_rank=32, lora_alpha=32, lora_quant_enable=False):

    type_support = {
        "linear": "<class 'torch.nn.modules.linear.Linear'>",
        "conv2d": "<class 'torch.nn.modules.conv.Conv2d'>",
    }
    with open(file_path, 'r', encoding='utf-8') as file:
        quant_configs = json.load(file)
    layers_strategy = quant_configs.get('layer_strategy')
    for layer in layers_strategy.keys():
        layer_strategy = layers_strategy.get(layer)
        if layer_strategy['type'] not in [type_support.get('linear'), type_support.get('conv2d')]:
            continue

        if layer_strategy['type'] == type_support.get('linear'):
            if layer.startswith('model.layers.'):
                layer_strategy['lora_config'] = {
                    "rank"  : lora_rank,
                    "alpha" : lora_alpha,
                    "quant_state": lora_quant_enable
                }

    with open(save_path, 'w', encoding='utf-8') as json_file:
        json.dump(quant_configs, json_file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    quant_config_set(
        "/home/ma-user/work/AIP_V/q30063898/quant_project/lora/1.7b_json/dopt_config.json",
        "/home/ma-user/work/AIP_V/q30063898/quant_project/lora/1.7b_json/dopt_config_withlora_rank8.json",
        lora_rank=8,
        lora_alpha=8
    )
