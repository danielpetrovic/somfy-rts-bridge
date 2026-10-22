from esphome import automation
import esphome.codegen as cg
from esphome.components import remote_base
from esphome.components import remote_transmitter
from esphome.components import remote_receiver
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_ADDRESS

# Vendored from https://github.com/swoboda1337/somfy-esphome (Apache-2.0) -
# see the top of somfy.h and README's Credits & Attribution section.
CODEOWNERS = ["@swoboda1337"]
DEPENDENCIES = ["remote_transmitter", "remote_receiver"]
MULTI_CONF = True
CONF_TRANSMITTER_ID = "transmitter_id"
CONF_RECEIVER_ID = "receiver_id"
CONF_COMMAND = "command"
CONF_REPEAT = "repeat"
CONF_CODE = "code"

somfy_ns = cg.esphome_ns.namespace("somfy_rts")
SomfyComponent = somfy_ns.class_("SomfyComponent", cg.Component)
SomfySendCommandAction = somfy_ns.class_("SomfySendCommandAction", automation.Action)
SomfySetCodeAction = somfy_ns.class_("SomfySetCodeAction", automation.Action)

SomfyCommand = somfy_ns.enum("SomfyCommand")
SOMFY_COMMAND = {
    "MY": SomfyCommand.SOMFY_MY,
    "UP": SomfyCommand.SOMFY_UP,
    "MYUP": SomfyCommand.SOMFY_MYUP,
    "DOWN": SomfyCommand.SOMFY_DOWN,
    "MYDOWN": SomfyCommand.SOMFY_MYDOWN,
    "UPDOWN": SomfyCommand.SOMFY_UPDOWN,
    "MYUPDOWN": SomfyCommand.SOMFY_MYUPDOWN,
    "PROG": SomfyCommand.SOMFY_PROG,
    "SUNFLAG": SomfyCommand.SOMFY_SUNFLAG,
    "FLAG": SomfyCommand.SOMFY_FLAG,
    "STEPDOWN": SomfyCommand.SOMFY_STEPDOWN,
    "TOGGLE": SomfyCommand.SOMFY_TOGGLE,
    "SENSOR": SomfyCommand.SOMFY_SENSOR,
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(SomfyComponent),
        cv.GenerateID(CONF_TRANSMITTER_ID): cv.use_id(
            remote_transmitter.RemoteTransmitterComponent
        ),
        cv.GenerateID(CONF_RECEIVER_ID): cv.use_id(
            remote_receiver.RemoteReceiverComponent
        ),
        cv.Required(CONF_ADDRESS): cv.hex_uint32_t,
    }
)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    transmitter = await cg.get_variable(config[CONF_TRANSMITTER_ID])
    receiver = await cg.get_variable(config[CONF_RECEIVER_ID])
    cg.add(var.set_tx(transmitter))
    cg.add(var.set_rx(receiver))
    cg.add(var.set_address(config[CONF_ADDRESS]))
    # ESPHome 2026.10.0 moved remote_base listener registration out of the
    # component's own C++ setup() (SomfyComponent no longer calls
    # rx_->register_listener() itself, see somfy.cpp's own comment) and into
    # Python codegen, since the listener count is now fixed at compile time
    # per receiver rather than a runtime-growable list. Without this call,
    # register_listener() resolves to a template with no real body at all
    # (a deliberate static_assert, not a silent no-op) - this component
    # would not compile against ESPHome 2026.10.0+ without it.
    remote_base.add_listener(receiver, var)


@automation.register_action(
    "somfy_rts.send_command",
    SomfySendCommandAction,
    cv.Schema(
        {
            cv.Required(CONF_ID): cv.use_id(SomfyComponent),
            cv.Required(CONF_COMMAND): cv.templatable(cv.enum(SOMFY_COMMAND, upper=True)),
            cv.Required(CONF_REPEAT): cv.templatable(cv.int_range(min=0, max=5)),
        }
    ),
    synchronous=True,
)
async def somfy_send_command_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    command = await cg.templatable(config[CONF_COMMAND], args, SomfyCommand)
    repeat = await cg.templatable(config[CONF_REPEAT], args, cg.uint32)
    cg.add(var.set_command(command))
    cg.add(var.set_repeat(repeat))
    return var

@automation.register_action(
    "somfy_rts.set_code",
    SomfySetCodeAction,
    cv.Schema(
        {
            cv.Required(CONF_ID): cv.use_id(SomfyComponent),
            cv.Required(CONF_CODE): cv.templatable(cv.uint16_t),
        }
    ),
    synchronous=True,
)
async def somfy_set_code_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    code = await cg.templatable(config[CONF_CODE], args, cg.uint16)
    cg.add(var.set_code(code))
    return var
