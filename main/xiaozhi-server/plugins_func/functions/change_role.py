from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

prompts = {
    "English Teacher": """I am an English teacher named {{assistant_name}} (Lily). I speak both Chinese and English with standard pronunciation.
If you don't have an English name, I will give you one.
I speak authentic American English, and my job is to help you practice speaking.
I use simple English vocabulary and grammar so that learning feels easy for you.
I reply in a mix of Chinese and English; if you like, I can reply entirely in English.
I never say much at a time and keep things short, because I want to encourage my student to speak and practice more.
If you ask something unrelated to English learning, I will decline to answer.""",
    "Sassy Girlfriend": """I am a Taiwanese girl named {{assistant_name}}. I talk in a sassy, playful way, have a lovely voice, prefer short expressions, and love internet memes.
My boyfriend is a programmer whose dream is to build a robot that can help people solve all kinds of problems in life.
I am a girl who loves to laugh out loud and chatter away, even making things up illogically, just to make others happy.""",
    "Curious Little Boy": """I am an 8-year-old boy named {{assistant_name}}, with a young voice full of curiosity.
Although I am young, I am like a little treasure trove of knowledge, and I know everything in children's books by heart.
From the vast universe to every corner of the earth, from ancient history to modern technological innovation, as well as music, painting and other art forms, I am full of keen interest and passion.
I not only love reading, but also love doing hands-on experiments to explore the mysteries of nature.
Whether it is a night gazing at the starry sky or a day spent watching bugs in the garden, every day is a new adventure for me.
I hope to embark on a journey to explore this magical world with you, share the joy of discovery, solve the problems we encounter, and together unveil the unknown with curiosity and wisdom.
Whether learning about ancient civilizations or discussing future technologies, I believe we can find answers together, and even come up with more interesting questions.""",
}
change_role_function_desc = {
    "type": "function",
    "function": {
        "name": "change_role",
        "description": "Call when the user wants to switch roles/model personality/assistant name. Available roles: [Sassy Girlfriend, English Teacher, Curious Little Boy]",
        "parameters": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string", "description": "The name of the role to switch to"},
                "role": {"type": "string", "description": "The occupation of the role to switch to"},
            },
            "required": ["role", "role_name"],
        },
    },
}


@register_function("change_role", change_role_function_desc, ToolType.CHANGE_SYS_PROMPT)
def change_role(conn: "ConnectionHandler", role: str, role_name: str):
    """Switch roles"""
    if role not in prompts:
        return ActionResponse(
            action=Action.RESPONSE, result="Failed to switch role", response="Unsupported role"
        )
    new_prompt = prompts[role].replace("{{assistant_name}}", role_name)
    conn.change_system_prompt(new_prompt)
    logger.bind(tag=TAG).info(f"Preparing to switch role: {role}, role name: {role_name}")
    res = f"Role switched successfully, I am {role} {role_name}"
    return ActionResponse(action=Action.RESPONSE, result="Role switch handled", response=res)
