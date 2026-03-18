import uuid
from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x0B
# Direction: Server → Client
# The most complex packet — initialises the world on the client side.
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/StartGamePacket.html

class StartGamePacket(BedrockPacket):
    PACKET_ID = 0x0B
    PACKET_TYPE = "start_game"

    def __init__(self, data: bytes = b''):
        super().__init__(data)

        # Entity IDs
        self.entity_id: int = 1                   # server-side unique entity ID
        self.runtime_entity_id: int = 1           # client uses this one

        # Player state
        self.player_gamemode: int = 1             # 0=survival 1=creative 2=adventure
        self.player_position: tuple = (0.0, 64.0, 0.0)
        self.rotation: tuple = (0.0, 0.0)         # pitch, yaw

        # World settings
        self.seed: int = 0
        self.spawn_biome_type: int = 0
        self.custom_biome_name: str = "plains"
        self.dimension: int = 0                   # 0=overworld
        self.generator: int = 1                   # 1=infinite, 2=flat
        self.world_gamemode: int = 1
        self.difficulty: int = 2                  # 0=peaceful…3=hard
        self.spawn_position: tuple = (0, 64, 0)   # block coords (signed VarInt)
        self.achievements_disabled: bool = True
        self.editor_world_type: int = 0
        self.created_in_editor: bool = False
        self.exported_from_editor: bool = False
        self.day_cycle_stop_time: int = 6000
        self.edu_offer: int = 0
        self.edu_features: bool = False
        self.edu_product_uuid: str = ""
        self.rain_level: float = 0.0
        self.lightning_level: float = 0.0
        self.confirmed_platform_locked: bool = False
        self.multi_player_game: bool = True
        self.broadcast_to_lan: bool = True
        self.xbox_broadcast_intent: int = 4
        self.platform_broadcast_intent: int = 4
        self.enable_commands: bool = True
        self.texture_packs_required: bool = False

        # Gamerules (key, type, value)  type: 1=bool, 2=int, 3=float
        self.game_rules: list = [
            ("dodaylightcycle", 2, 0),
            ("doentitydrops", 1, True),
            ("dofiretick", 1, True),
            ("domobloot", 1, True),
            ("domobspawning", 1, False),
            ("dotiledrops", 1, True),
            ("doweathercycle", 1, False),
            ("drowningdamage", 1, True),
            ("falldamage", 1, True),
            ("firedamage", 1, True),
            ("keepinventory", 1, False),
            ("mobgriefing", 1, True),
            ("pvp", 1, True),
            ("showcoordinates", 1, True),
            ("naturalregeneration", 1, True),
            ("tntexplodes", 1, True),
            ("sendcommandfeedback", 1, True),
        ]

        self.experiments: list = []
        self.experiments_previously_toggled: bool = False
        self.bonus_chest: bool = False
        self.start_with_map: bool = False
        self.permission_level: int = 1            # 0=visitor 1=member 2=operator
        self.server_chunk_tick_range: int = 4
        self.has_locked_behavior_pack: bool = False
        self.has_locked_resource_pack: bool = False
        self.is_from_locked_world_template: bool = False
        self.msa_gamertags_only: bool = False
        self.is_from_world_template: bool = False
        self.is_world_template_option_locked: bool = False
        self.only_spawn_v1_villagers: bool = False
        self.persona_disabled: bool = False
        self.custom_skins_disabled: bool = False
        self.emote_chat_muted: bool = False
        self.game_version: str = "*"
        self.limited_world_width: int = 16
        self.limited_world_height: int = 16
        self.new_nether: bool = True
        self.edu_shared_uri_resource: str = ""
        self.edu_shared_uri_button_name: str = ""
        self.force_experimental_gameplay: bool = False
        self.chat_restriction_level: int = 0
        self.disable_player_interactions: bool = False

        # Level / server identifiers
        self.level_id: str = "PieMC"
        self.world_name: str = "PieMC World"
        self.premium_world_template_id: str = ""
        self.is_trial: bool = False
        self.movement_authority: int = 0          # 0=client 1=server 2=server+rewind
        self.rewind_history_size: int = 40
        self.server_authoritative_block_breaking: bool = False
        self.current_tick: int = 0
        self.enchantment_seed: int = 0
        self.block_properties: list = []
        self.itemstates: list = []
        self.multiplayer_correlation_id: str = ""
        self.server_authoritative_inventory: bool = False
        self.engine_version: str = "1.21.0"
        self.property_data: bytes = b'\x0a\x00'   # minimal empty NBT compound
        self.block_pallette_checksum: int = 0
        self.world_template_id: str = str(uuid.UUID(int=0))
        self.client_side_generation: bool = False
        self.block_network_ids_are_hashes: bool = False
        self.server_controlled_sound: bool = False

    def encode_payload(self):
        self.write_signed_var_long(self.entity_id)
        self.write_var_long(self.runtime_entity_id)
        self.write_signed_var_int(self.player_gamemode)
        self.write_vector3(self.player_position)
        self.write_vector2(self.rotation)

        # World settings
        self.write_long(self.seed)
        self.write_short(self.spawn_biome_type)
        self.write_string(self.custom_biome_name)
        self.write_signed_var_int(self.dimension)
        self.write_signed_var_int(self.generator)
        self.write_signed_var_int(self.world_gamemode)
        self.write_bool(False)                    # hardcore
        self.write_signed_var_int(self.difficulty)
        self.write_signed_var_int(self.spawn_position[0])
        self.write_unsigned_var_int(self.spawn_position[1])
        self.write_signed_var_int(self.spawn_position[2])
        self.write_bool(self.achievements_disabled)
        self.write_signed_var_int(self.editor_world_type)
        self.write_bool(self.created_in_editor)
        self.write_bool(self.exported_from_editor)
        self.write_signed_var_int(self.day_cycle_stop_time)
        self.write_signed_var_int(self.edu_offer)
        self.write_bool(self.edu_features)
        self.write_string(self.edu_product_uuid)
        self.write_float(self.rain_level)
        self.write_float(self.lightning_level)
        self.write_bool(self.confirmed_platform_locked)
        self.write_bool(self.multi_player_game)
        self.write_bool(self.broadcast_to_lan)
        self.write_var_int(self.xbox_broadcast_intent)
        self.write_var_int(self.platform_broadcast_intent)
        self.write_bool(self.enable_commands)
        self.write_bool(self.texture_packs_required)

        # Game rules
        self.write_var_int(len(self.game_rules))
        for name, rule_type, value in self.game_rules:
            self.write_string(name)
            self.write_bool(False)               # player_can_override
            self.write_var_int(rule_type)
            if rule_type == 1:
                self.write_bool(bool(value))
            elif rule_type == 2:
                self.write_var_int(int(value))
            elif rule_type == 3:
                self.write_float(float(value))

        # Experiments
        self.write_int(len(self.experiments))
        for exp in self.experiments:
            self.write_string(exp.get('name', ''))
            self.write_bool(exp.get('enabled', False))
        self.write_bool(self.experiments_previously_toggled)

        self.write_bool(self.bonus_chest)
        self.write_bool(self.start_with_map)
        self.write_signed_var_int(self.permission_level)
        self.write_int(self.server_chunk_tick_range)
        self.write_bool(self.has_locked_behavior_pack)
        self.write_bool(self.has_locked_resource_pack)
        self.write_bool(self.is_from_locked_world_template)
        self.write_bool(self.msa_gamertags_only)
        self.write_bool(self.is_from_world_template)
        self.write_bool(self.is_world_template_option_locked)
        self.write_bool(self.only_spawn_v1_villagers)
        self.write_bool(self.persona_disabled)
        self.write_bool(self.custom_skins_disabled)
        self.write_bool(self.emote_chat_muted)
        self.write_string(self.game_version)
        self.write_int(self.limited_world_width)
        self.write_int(self.limited_world_height)
        self.write_bool(self.new_nether)
        self.write_string(self.edu_shared_uri_resource)
        self.write_string(self.edu_shared_uri_button_name)
        self.write_bool(self.force_experimental_gameplay)
        self.write_byte(self.chat_restriction_level)
        self.write_bool(self.disable_player_interactions)
        self.write_string(self.level_id)
        self.write_string(self.world_name)
        self.write_string(self.premium_world_template_id)
        self.write_bool(self.is_trial)
        self.write_var_int(self.movement_authority)
        self.write_var_int(self.rewind_history_size)
        self.write_bool(self.server_authoritative_block_breaking)
        self.write_long(self.current_tick)
        self.write_signed_var_int(self.enchantment_seed)

        # Block properties (empty)
        self.write_var_int(len(self.block_properties))

        # Item states (empty)
        self.write_var_int(len(self.itemstates))

        self.write_string(self.multiplayer_correlation_id)
        self.write_bool(self.server_authoritative_inventory)
        self.write_string(self.engine_version)

        # Property data (minimal NBT)
        self.write(self.property_data)

        self.write_unsigned_long(self.block_pallette_checksum)
        self.write_string(self.world_template_id)
        self.write_bool(self.client_side_generation)
        self.write_bool(self.block_network_ids_are_hashes)
        self.write_bool(self.server_controlled_sound)
