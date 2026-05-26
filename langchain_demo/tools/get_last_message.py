# 获取最后用户消息
def get_last_user_after_assistant(history):
    """反向遍历找到最后一个assistant的位置，并返回后面的所有user消息"""
    if not history:
        return None
    if history[-1]['role'] == 'assistant':
        return None

    last_assistant_index = -1
    for i in range(len(history)-1,-1,-1):
        if history[i]['role'] == 'assistant':
            last_assistant_index = i
            break

    # 如果没有找到assistant
    if last_assistant_index == -1:
        return history
    else:
        # 从assistant位置向后查找第一个user
        return history[last_assistant_index+1:]