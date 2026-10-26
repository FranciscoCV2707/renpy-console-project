init -999 python:
    import os as _rcp_os

    _rcp_out_path = _rcp_os.environ.get("RCP_TRACE_OUT")
    _rcp_enabled = [False]
    _rcp_file = [None]
    _rcp_seq = [0]
    _rcp_frame = [0]
    _rcp_prev_tags = [None]
    _rcp_prev_music = [None]
    _rcp_pending_say = [None]

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

    def _rcp_loc():
        result = None
        try:
            result = renpy.get_filename_line()
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))
            result = None
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
        try:
            tags = renpy.get_showing_tags("master")
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))
            tags = None
        if tags is None:
            try:
                tags = renpy.game.context().images.get_showing_tags("master")
            except Exception as e:
                _rcp_emit("ERROR", msg=str(e))
                tags = None
        if tags is None:
            tags = []
        try:
            return list(tags)
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))
            return []

    def _rcp_music():
        music = None
        try:
            music = renpy.music.get_playing("music")
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))
            music = None
        return music

    def _rcp_get_who():
        holders = [getattr(renpy, "store", None), renpy]
        for holder in holders:
            if holder is None:
                continue
            if not hasattr(holder, "_last_say_who"):
                continue
            value = getattr(holder, "_last_say_who")
            if value is None:
                continue
            if hasattr(value, "name"):
                return value.name
            if isinstance(value, str) and hasattr(renpy, "eval_who"):
                try:
                    obj = renpy.eval_who(value)
                    if hasattr(obj, "name"):
                        return obj.name
                except Exception as e:
                    _rcp_emit("ERROR", msg=str(e))
            return value
        return None

    def _rcp_on_label(name, abnormal=False):
        if not _rcp_enabled[0]:
            return
        try:
            _rcp_emit("LABEL", name=name)
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))

    def _rcp_on_interact():
        if not _rcp_enabled[0]:
            return
        try:
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
                fields = {"tag": tag}
                if hasattr(renpy, "get_attributes"):
                    try:
                        fields["attrs"] = renpy.get_attributes(tag)
                    except Exception as e:
                        _rcp_emit("ERROR", msg=str(e))
                _rcp_emit("SHOW", **fields)
            _rcp_prev_tags[0] = curr_tags

            curr_music = _rcp_music()
            prev_music = _rcp_prev_music[0]
            if curr_music != prev_music:
                if curr_music:
                    _rcp_emit("PLAY", music=curr_music)
                else:
                    _rcp_emit("STOP", music=prev_music if prev_music is not None else "")
            _rcp_prev_music[0] = curr_music

            pending = _rcp_pending_say[0]
            if pending is not None:
                who, loc = pending
                _rcp_emit("SAY", who=who, loc=loc)
                _rcp_pending_say[0] = None
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))

    def _rcp_on_say(event=None, interact=True, **kwargs):
        if not _rcp_enabled[0]:
            return
        if event not in (None, "begin"):
            return
        if interact is False:
            who = kwargs.get("who", kwargs.get("character", None))
            if who is None:
                who = _rcp_get_who()
            if who is None:
                who = ""
            loc = kwargs.get("loc", None)
            if loc is None:
                loc = _rcp_loc()
            _rcp_emit("SAY", who=who, loc=loc)
            return
        who = kwargs.get("who", kwargs.get("character", None))
        if who is None:
            who = _rcp_get_who()
        if who is None:
            who = ""
        loc = kwargs.get("loc", None)
        if loc is None:
            loc = _rcp_loc()
        _rcp_pending_say[0] = (who, loc)

    _rcp_original_display_menu = getattr(getattr(renpy, "exports", None), "display_menu", None)
    if _rcp_original_display_menu is None:
        _rcp_original_display_menu = getattr(renpy, "display_menu", None)

    def _rcp_display_menu(items, *args, **kwargs):
        if not _rcp_enabled[0]:
            if _rcp_original_display_menu is not None:
                return _rcp_original_display_menu(items, *args, **kwargs)
            return None
        _rcp_emit("MENU", loc=_rcp_loc())
        result = None
        if _rcp_original_display_menu is not None:
            result = _rcp_original_display_menu(items, *args, **kwargs)

        options = []
        for item in items or []:
            if isinstance(item, (tuple, list)):
                label = item[0] if len(item) > 0 else None
                value = item[1] if len(item) > 1 else None
            else:
                label = item
                value = item
            vv = getattr(value, "value", value)
            if value is None or vv is None:
                continue
            if hasattr(value, "sensitive") and not value.sensitive:
                continue
            options.append((label, value))

        idx = None
        if result is not None:
            for pos, (label, value) in enumerate(options):
                vv = getattr(value, "value", value)
                if result == vv or result == value or result == label:
                    idx = pos
                    break
        if idx is not None:
            _rcp_emit("CHOICE", i=idx)
        return result

    if _rcp_original_display_menu is not None:
        if hasattr(renpy, "exports"):
            renpy.exports.display_menu = _rcp_display_menu
        if hasattr(renpy, "display_menu"):
            renpy.display_menu = _rcp_display_menu
    _rcp_store_mod = getattr(renpy, "store", None)
    if _rcp_store_mod is not None and hasattr(_rcp_store_mod, "menu"):
        _rcp_store_mod.menu = _rcp_display_menu

    if _rcp_out_path:
        _rcp_enabled[0] = True
        _dir = _rcp_os.path.dirname(_rcp_out_path)
        if _dir:
            _rcp_os.makedirs(_dir, exist_ok=True)
        _rcp_file[0] = open(_rcp_out_path, "w", encoding="utf-8")

    if not hasattr(config, "label_callbacks"):
        config.label_callbacks = []
    config.label_callbacks.append(_rcp_on_label)
    if not hasattr(config, "start_interact_callbacks"):
        config.start_interact_callbacks = []
    config.start_interact_callbacks.append(_rcp_on_interact)
    if not hasattr(config, "all_character_callbacks"):
        config.all_character_callbacks = []
    config.all_character_callbacks.append(_rcp_on_say)