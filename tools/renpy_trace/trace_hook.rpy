init -999 python:
    import os as _rcp_os

    _rcp_out_path = _rcp_os.environ.get("RCP_TRACE_OUT")
    _rcp_enabled = [False]
    _rcp_file = [None]
    _rcp_seq = [0]
    _rcp_frame = [0]
    _rcp_prev_tags = [None]
    _rcp_prev_music = [None]

    def _rcp_escape(value):
        if value is None:
            s = ""
        else:
            s = str(value)
        s = s.replace("\\", "\\\\")
        s = s.replace("\r", "\\r")
        s = s.replace("\n", "\\n")
        s = s.replace("|", "\\|")
        s = s.replace(";", "\\;")
        s = s.replace("=", "\\=")
        return s

    _escape = _rcp_escape
    _escape_value = _rcp_escape
    _rcp_escape_value = _rcp_escape

    def _rcp_loc():
        result = None
        for call in (
            lambda: renpy.get_filename_line(),
            lambda: renpy.get_filename_line,
        ):
            try:
                result = call()
                break
            except Exception:
                result = None
        if result is None and hasattr(renpy, "_loc"):
            result = getattr(renpy, "_loc")
        if result is None:
            return ""
        if isinstance(result, (tuple, list)) and len(result) >= 2:
            filename, line = result[0], result[1]
        elif isinstance(result, str):
            return result
        else:
            return str(result)
        path = str(filename).replace("\\", "/")
        return "%s:%s" % (path, line)

    def _rcp_showing_tags():
        tags = None
        for call in (
            lambda: renpy.get_showing_tags("master"),
            lambda: renpy.get_showing_tags(layer="master"),
            lambda: renpy.get_showing_tags(),
        ):
            try:
                tags = call()
                break
            except Exception:
                tags = None
        if tags is None:
            for attr in ("_tags", "showing_tags", "master_tags"):
                if hasattr(renpy, attr):
                    tags = getattr(renpy, attr)
                    break
        if tags is None:
            for path in (
                lambda: renpy.game.context().images.get_showing_tags("master"),
                lambda: renpy.game.context().scene_lists.get_showing_tags("master"),
            ):
                try:
                    tags = path()
                    break
                except Exception:
                    tags = None
        if tags is None:
            tags = []
        try:
            return list(tags)
        except Exception:
            return []

    def _rcp_music():
        for call in (
            lambda: renpy.music.get_playing("music"),
            lambda: renpy.get_playing_music(),
        ):
            try:
                return call()
            except Exception:
                pass
        for attr in ("_music", "playing_music", "current_music"):
            if hasattr(renpy, attr):
                return getattr(renpy, attr)
        return None

    def _rcp_get_who():
        holders = [getattr(renpy, "store", None), renpy]
        for holder in holders:
            if holder is None:
                continue
            for attr in ("_last_say_who", "_who", "last_say_who"):
                if hasattr(holder, attr):
                    value = getattr(holder, attr)
                    if value is not None:
                        return value
        return None

    def _rcp_emit(ev, **fields):
        if not _rcp_enabled[0] or _rcp_file[0] is None:
            return
        _rcp_seq[0] += 1
        seq = _rcp_seq[0]
        frame = _rcp_frame[0]
        pairs = ["%s=%s" % (k, _rcp_escape(v)) for k, v in fields.items()]
        if pairs:
            line = "T|%d|%d|%s|%s" % (seq, frame, ev, ";".join(pairs))
        else:
            line = "T|%d|%d|%s" % (seq, frame, ev)
        _rcp_file[0].write(line + "\n")
        _rcp_file[0].flush()

    _emit = _rcp_emit

    def _rcp_on_label(name, abnormal=False):
        if not _rcp_enabled[0]:
            return
        _rcp_emit("LABEL", name=name)

    def _rcp_on_interact():
        if not _rcp_enabled[0]:
            return
        _rcp_frame[0] += 1
        curr_tags = set(_rcp_showing_tags())
        prev = _rcp_prev_tags[0]
        if prev is None:
            prev = set()
        else:
            prev = set(prev)
        removed = prev - curr_tags
        added = curr_tags - prev
        if prev and removed == prev:
            _rcp_emit("SCENE")
        for tag in sorted(removed):
            if not (prev and removed == prev):
                _rcp_emit("HIDE", tag=tag)
        for tag in sorted(added):
            _rcp_emit("SHOW", tag=tag)
        _rcp_prev_tags[0] = curr_tags

        curr_music = _rcp_music()
        prev_music = _rcp_prev_music[0]
        if curr_music != prev_music:
            if curr_music:
                _rcp_emit("PLAY", music=curr_music)
            else:
                _rcp_emit("STOP", music=prev_music if prev_music is not None else "")
        _rcp_prev_music[0] = curr_music

    def _rcp_on_say(event=None, interact=True, **kwargs):
        if not _rcp_enabled[0]:
            return
        if event not in (None, "begin"):
            return
        if interact is False:
            return
        who = kwargs.get("who", kwargs.get("character", None))
        if who is None:
            who = _rcp_get_who()
        if who is None:
            who = ""
        loc = kwargs.get("loc", None)
        if loc is None:
            loc = _rcp_loc()
        _rcp_emit("SAY", who=who, loc=loc)

    _rcp_say = _rcp_on_say
    _on_say = _rcp_on_say

    _rcp_original_display_menu = None
    try:
        _rcp_original_display_menu = renpy.exports.display_menu
    except Exception:
        try:
            _rcp_original_display_menu = getattr(renpy, "display_menu", None)
        except Exception:
            _rcp_original_display_menu = None

    def _rcp_display_menu(items, *args, **kwargs):
        if not _rcp_enabled[0]:
            if _rcp_original_display_menu is not None:
                return _rcp_original_display_menu(items, *args, **kwargs)
            return None
        _rcp_emit("MENU", loc=_rcp_loc())
        result = None
        if _rcp_original_display_menu is not None:
            result = _rcp_original_display_menu(items, *args, **kwargs)
        idx = None
        try:
            for i, item in enumerate(items or []):
                if isinstance(item, (tuple, list)):
                    label = item[0] if len(item) > 0 else None
                    value = item[1] if len(item) > 1 else None
                else:
                    label = item
                    value = item
                vv = getattr(value, "value", value)
                if result == vv or result == label:
                    idx = i
                    break
        except Exception:
            idx = None
        if idx is None and items:
            idx = 0
        _rcp_emit("CHOICE", i=idx if idx is not None else 0)
        return result

    if _rcp_original_display_menu is not None:
        try:
            renpy.exports.display_menu = _rcp_display_menu
        except Exception:
            pass
        try:
            renpy.display_menu = _rcp_display_menu
        except Exception:
            pass
    try:
        import store as _rcp_store_mod
        if hasattr(_rcp_store_mod, "menu"):
            _rcp_store_mod.menu = _rcp_display_menu
    except Exception:
        pass

    if _rcp_out_path:
        _rcp_enabled[0] = True
        try:
            _dir = _rcp_os.path.dirname(_rcp_out_path)
            if _dir:
                _rcp_os.makedirs(_dir, exist_ok=True)
        except Exception:
            pass
        try:
            _rcp_file[0] = open(_rcp_out_path, "w", encoding="utf-8")
        except Exception:
            _rcp_enabled[0] = False
            _rcp_file[0] = None

    if not hasattr(config, "label_callbacks"):
        config.label_callbacks = []
    config.label_callbacks.append(_rcp_on_label)
    if not hasattr(config, "start_interact_callbacks"):
        config.start_interact_callbacks = []
    config.start_interact_callbacks.append(_rcp_on_interact)
    if not hasattr(config, "all_character_callbacks"):
        config.all_character_callbacks = []
    config.all_character_callbacks.append(_rcp_on_say)