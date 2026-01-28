import argparse
from aigc_detection import detect_aigc_in_text, detect_aigc_in_file
from aigc_detection import save_annotated_result


def run(args):
    while True:
        print("\n请选择输入方式：")
        input_type = input("1: 输入文本  2: 输入文件  3: 退出\n")

        if input_type == '1':
            print("请输入文本内容（输入两次回车结束）：\n")
            user_input = []
            
            while True:
                line = input()
                if line == "":  # 检测到空行
                    if len(user_input) > 0 and user_input[-1] == "":  # 连续两次空行
                        break
                user_input.append(line)

            text = "\n".join(user_input).strip()  # 组合成完整文本，去除前后空白
            if text:
                result = detect_aigc_in_text(text, args)
                print("\n检测结果：")
                print(result)
            else:
                print("输入为空，请重新输入文本。")

        elif input_type == '2':
            file_path = input("请输入文件路径：\n")
            output_path = input("请输入输出文件路径（包括文件名和扩展名）：\n")
            original_text, result_text = detect_aigc_in_file(file_path, args)
            # 传递两个参数给 save_annotated_result
            save_annotated_result(original_text, result_text, output_path)

        elif input_type == '3':
            print("程序已退出。")
            break  # 退出循环，结束程序

        else:
            print("无效输入，请重新选择。")
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference_model_name', type=str, default="gpt-neo-2.7B")  # use gpt-j-6B for more accurate detection
    parser.add_argument('--scoring_model_name', type=str, default="gpt-neo-2.7B")
    parser.add_argument('--dataset', type=str, default="xsum")
    parser.add_argument('--ref_path', type=str, default="/root/Fast-DetectGPT/fast-detect-gpt/local_infer_ref")
    parser.add_argument('--device', type=str, default="cuda")
    parser.add_argument('--cache_dir', type=str, default="../cache")
    args = parser.parse_args()

    run(args)
