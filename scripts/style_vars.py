import logging
import re

# import gradio as gr
from gradio.components import Component
from modules import shared, script_callbacks, scripts
from modules.processing import StableDiffusionProcessing, StableDiffusionProcessingTxt2Img


# variables
logger = logging.getLogger("style_vars")
logger.setLevel(logging.INFO)

extn_name = "Style Variables"
extn_id = "style_vars"
extn_enabled = extn_id + "_enabled"

var_char = "$"


# regexes
re_prompt = re.compile(r",? *\{prompt\} *,? *", re.I)


# helper functions
def build_var(name: str):
    if " " in name:
        return f"{var_char}({name})"
    return f"{var_char}{name}"

def on_ui_settings():
    section = (extn_id, extn_name)
    shared.opts.add_option(extn_enabled, shared.OptionInfo(True, f"Enable extension", section=section))


# register callbacks
script_callbacks.on_ui_settings(on_ui_settings)
# script_callbacks.on_infotext_pasted(infotext_pasted_cb)


class StyleVars(scripts.Script):
    is_txt2img: bool = False

    infotext_fields: list[tuple[Component, str]] = []

    def title(self):
        return extn_name

    def show(self, is_img2img: bool):
        return scripts.AlwaysVisible

    # def ui(self, is_img2img: bool) -> list[Component]:
    #     with gr.Accordion(label=extn_name, open=False):
    #         with gr.Row(elem_id=f"{extn_id}_row"):
    #             enabled = gr.Checkbox(
    #                 label="Enabled",
    #                 value=True,
    #                 description="Enable prompt processing",
    #                 elem_id=f"{extn_id}_enabled",
    #                 scale=1,
    #             )
    #     return [enabled]

    def process(
        self,
        p: StableDiffusionProcessing,
        *args,
    ):
        if getattr(shared.opts, extn_enabled) is not True:
            return
        style_names: list[str] = shared.prompt_styles.styles.keys()

        def rewrite_prompt(prompt: str, neg: bool):
            for name in style_names:
                if name not in prompt:
                    continue
                mode = 2 if neg else 1
                
                # normal vars
                text = shared.prompt_styles.styles[name][mode]
                parts = re_prompt.split(text)
                text = ", ".join(parts)
                if " " not in name:
                    prompt = prompt.replace(f"{var_char}{name}", text)
                prompt = prompt.replace(f"{var_char}({name})", text)
                
                # split vars
                for i, part in enumerate(parts):
                    if " " not in name:
                        prompt = prompt.replace(f"{var_char}{i+1}{name}", part)
                    prompt = prompt.replace(f"{var_char}{i+1}({name})", part)
            
            # return the rewritten prompt
            return prompt

        # check if we're doing t2i with HR
        is_t2i = isinstance(p, StableDiffusionProcessingTxt2Img)
        hr_enabled = p.enable_hr if is_t2i else False

        logger.info(f"{extn_name} processing...")

        batch_size = p.batch_size
        for b_idx in range(p.n_iter):
            for s_offs in range(batch_size):
                s_idx = b_idx * batch_size + s_offs  # offset of the prompt in all_prompts

                s_prompt = rewrite_prompt(p.all_prompts[s_idx], False)
                p.all_prompts[s_idx] = s_prompt
                logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] prompt: {s_prompt}")

                s_neg_prompt = rewrite_prompt(p.all_negative_prompts[s_idx], True)
                p.all_negative_prompts[s_idx] = s_neg_prompt
                logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] neg prompt: {s_neg_prompt}")

                if is_t2i and hr_enabled:
                    s_hr_prompt = rewrite_prompt(p.all_hr_prompts[s_idx], False)
                    p.all_hr_prompts[s_idx] = s_hr_prompt
                    if s_hr_prompt != s_prompt:
                        logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] HR prompt: {s_hr_prompt}")

                    s_hr_neg_prompt = rewrite_prompt(p.all_hr_negative_prompts[s_idx], True)
                    p.all_hr_negative_prompts[s_idx] = s_hr_neg_prompt
                    if s_hr_neg_prompt != s_neg_prompt:
                        logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] HR neg prompt: {s_hr_neg_prompt}")

        logger.info(f"{extn_name} processing done.")


# def infotext_pasted_cb(prompt: str, params: dict[str, str]):
#     if TS_PROMPT in params:
#         params["Prompt"] = params.get(TS_PROMPT, params["Prompt"])

#     if TS_NEGATIVE in params:
#         params["Negative prompt"] = params.get(TS_NEGATIVE, params["Negative prompt"])
