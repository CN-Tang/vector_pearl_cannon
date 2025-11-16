from mcdreforged.api.all import *

PLUGIN_METADATA = {
    'id': 'vector_pearl_cannon',
    'version': '1.0.0',
    'name': 'Vector Pearl Cannon Calculator',
    'description': 'A Minecraft Pearl Cannon ROM encoding conversion plugin based on MCDR',
    'author': 'CN-Tang',
    'link': 'https://github.com/CN-Tang/vector_pearl_cannon',
    'dependencies': {
        'mcdreforged': '>=2.0.0'
    }
}

# 原始权重数组 - 不按顺序
BLUE_WEIGHTS_ORIGINAL = [1, 2, 3, 4, 10, 20, 40, 80, 160, 300, 600, 4800, 2400, 1200, 6000]
RED_WEIGHTS_ORIGINAL = [6000, 1200, 1200, 4800, 600, 300, 160, 80, 40, 20, 10, 4, 3, 2, 1]

# 方向到二进制代码的映射
DIRECTION_MAP = {
    'east': '00',
    'north': '01',
    'south': '10',
    'west': '11'
}


def calculate_binary_sequence(value, original_weights):
    """
    根据给定的权重数组计算二进制序列
    计算时按从大到小排序，但输出保持原始顺序
    """
    if value < 0:
        raise ValueError(f"Value {value} cannot be negative")

    # 创建权重和索引的配对
    indexed_weights = [(weight, idx) for idx, weight in enumerate(original_weights)]

    # 按权重从大到小排序
    sorted_weights = sorted(indexed_weights, key=lambda x: x[0], reverse=True)

    remaining = value
    # 初始化二进制列表，全部为0
    binary_list = ['0'] * len(original_weights)

    # 按照从大到小的顺序处理权重
    for weight, original_idx in sorted_weights:
        if remaining >= weight:
            binary_list[original_idx] = '1'
            remaining -= weight

    if remaining != 0:
        raise ValueError(f"Cannot represent {value} with given weights. Remainder: {remaining}")

    return ''.join(binary_list)


def format_binary_sequence(blue_binary, direction_code, red_binary):
    """
    将二进制序列格式化为分组显示
    """
    # 蓝色部分：每3位一组
    blue_groups = []
    for i in range(0, 15, 3):
        blue_groups.append(blue_binary[i:i + 3])

    # 红色部分：每3位一组
    red_groups = []
    for i in range(0, 15, 3):
        red_groups.append(red_binary[i:i + 3])

    formatted = ' '.join(blue_groups) + ' ' + direction_code + ' ' + ' '.join(red_groups)
    return formatted


def show_help(source: CommandSource):
    """
    显示帮助信息
    """
    help_text = '''
§6========== XTS服务器矢量珍珠炮转译码工具 ==========
§b使用方法:
§a!!ftl <蓝色TNT数量> <方向> <红色TNT数量>§r - 计算二进制编码序列
§a!!ftl help§r - 显示此帮助信息

§e参数说明:
§6蓝色TNT数量§r: 0-12000的整数
§6方向§r: east, north, south, west
§6红色TNT数量§r: 0-12000的整数

§e示例:
§7!!ftl 291 west 568§r - 计算蓝291、西方向、红568的编码

§e输出格式:
蓝色二进制(15位分组) 方向(2位) 红色二进制(15位分组)
§6========================================
    '''
    source.reply(help_text)


def create_calculate_handler(direction):
    """
    为每个方向创建处理函数
    """

    def handler(source: CommandSource, ctx: dict):
        try:
            blue_tnt = ctx['blue_tnt']
            red_tnt = ctx['red_tnt']

            # 计算蓝色二进制序列
            blue_binary = calculate_binary_sequence(blue_tnt, BLUE_WEIGHTS_ORIGINAL)

            # 计算红色二进制序列
            red_binary = calculate_binary_sequence(red_tnt, RED_WEIGHTS_ORIGINAL)

            direction_code = DIRECTION_MAP[direction]
            full_binary = blue_binary + direction_code + red_binary
            formatted_binary = format_binary_sequence(blue_binary, direction_code, red_binary)

            source.reply('§6========== XTS服务器矢量珍珠炮转译码工具 ==========')
            source.reply(f'§b蓝色TNT: §a{blue_tnt}§r')
            source.reply(f'§b方向: §a{direction}§r → §e{direction_code}§r')
            source.reply(f'§b红色TNT: §c{red_tnt}§r')
            source.reply(f'§b完整32位二进制: §e{full_binary}§r')
            source.reply(f'§b格式化输出: §a{formatted_binary}§r')

            # 验证计算
            blue_calculated = sum(BLUE_WEIGHTS_ORIGINAL[i] for i, bit in enumerate(blue_binary) if bit == '1')
            red_calculated = sum(RED_WEIGHTS_ORIGINAL[i] for i, bit in enumerate(red_binary) if bit == '1')
            source.reply(f'§b验证: 蓝{blue_calculated} + 红{red_calculated} = 总计{blue_calculated + red_calculated}§r')

            source.reply('§6======================================')

        except ValueError as e:
            source.reply(f'§c计算错误: {e}')
            source.reply('§e提示: 尝试使用不同的TNT数量组合')
        except Exception as e:
            source.reply(f'§c发生未知错误: {e}')

    return handler


def on_load(server: PluginServerInterface, old):
    """
    插件加载时执行
    """
    server.register_help_message('!!ftl', 'XTS服务器矢量珍珠炮转译码工具')

    # 创建命令树
    command_tree = Literal('!!ftl'). \
        runs(lambda src: show_help(src)). \
        then(Literal('help').runs(show_help))

    # 为每个方向创建命令分支
    directions = ['east', 'north', 'south', 'west']
    for direction in directions:
        command_tree = command_tree.then(
            Integer('blue_tnt').at_min(0).at_max(12000).
            then(Literal(direction).
                 then(Integer('red_tnt').at_min(0).at_max(12000).
                      runs(create_calculate_handler(direction))
                      )
                 )
        )

    server.register_command(command_tree)
    server.logger.info('XTS服务器矢量珍珠炮转译码插件加载成功！')
    server.logger.info(f'蓝色权重(原始顺序): {BLUE_WEIGHTS_ORIGINAL}')
    server.logger.info(f'红色权重(原始顺序): {RED_WEIGHTS_ORIGINAL}')


def on_unload(server: PluginServerInterface):
    """
    插件卸载时执行
    """
    server.logger.info('XTS服务器矢量珍珠炮转译码插件已卸载')