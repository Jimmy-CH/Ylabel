from copy import deepcopy


def merge_labels_with_transcription(labels_list, transcription_list):
    """
    将 transcription 的 text 合并到 labels 中，按索引一一对应。
    返回新的 labels 列表，每个元素包含原字段 + 'text'
    """
    if len(labels_list) != len(transcription_list):
        # 如果长度不一致，可选：跳过或报错
        return labels_list  # 或 raise ValueError

    merged = []
    for lab, trans in zip(labels_list, transcription_list):
        new_lab = deepcopy(lab)
        new_lab['text'] = trans.get('text', [])
        merged.append(new_lab)
    return merged

