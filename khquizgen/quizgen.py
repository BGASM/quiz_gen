import khquizgen as kh


def main(input_path=None, output_path=None):
    kh.logger.debug("Main function called.")
    inputs = input_path if input_path else kh.INPUTS_PATH
    outputs = output_path if output_path else kh.OUTPUTS_PATH
    data = kh.parse_questions.run(inputs_path=inputs, outputs_path=outputs)
    quiz = kh.gen_quiz.run(data, 100)
    verify = kh.use_template.run(quiz=quiz, outputs_path=outputs)
    return verify
