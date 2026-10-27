init -999 python:
    import os as _rcp_os

    _rcp_out_path = _rcp_os.environ.get("RCP_TRACE_OUT")
    _rcp_enabled = [False]
    _rcp_file = [None]
    _rcp_seq = [0]
    _rcp_frame = [0]
    _rcp_prev_tags = [None]
    _rcp_prev_attrs = [{}]
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
        try:
            filename, line = renpy.get_filename_line()
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))
            return ""
        path = str(filename).replace("\\", "/")
        return "%s:%s" % (path, line)

    def _rcp_showing_tags():
        try:
            return renpy.get_showing_tags("master")
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))
            return []

    # La musica sale de las ordenes play/stop del guion, no del canal: con "stop music fadeout 3" get_playing sigue
    # devolviendo la pista mientras se desvanece y, con el avance automatico, eso son varias lineas de mas.
    _rcp_music_cmd = [None]
    _rcp_orig_play = renpy.music.play
    _rcp_orig_stop = renpy.music.stop

    def _rcp_play(filenames, channel="music", *args, **kwargs):
        if channel == "music":
            names = [filenames] if isinstance(filenames, str) else list(filenames or [])
            _rcp_music_cmd[0] = names[0] if names else None
        return _rcp_orig_play(filenames, channel, *args, **kwargs)

    def _rcp_stop(channel="music", *args, **kwargs):
        if channel == "music":
            _rcp_music_cmd[0] = None
        return _rcp_orig_stop(channel, *args, **kwargs)

    renpy.music.play = _rcp_play
    renpy.music.stop = _rcp_stop

    def _rcp_music():
        return _rcp_music_cmd[0]

    def _rcp_get_who():
        if renpy.store._last_say_who is None:
            return ""
        # Un personaje escrito como texto ("Trevor & Tana" "...") llega como str, sin .name. El nombre se traduce como
        # al mostrarlo (renpy.translate_string, exports/__init__.py:277 del SDK 8.3.7): PS1 lo tiene en español
        who = renpy.eval_who(renpy.store._last_say_who)
        return renpy.translate_string(who if isinstance(who, str) else who.name)

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
            # SHOW tambien cuando un tag ya visible cambia de expresion (antes solo al aparecer)
            attrs = {}
            for tag in sorted(curr_tags):
                attrs[tag] = " ".join(renpy.get_attributes(tag) or ())
                if tag in added or attrs[tag] != _rcp_prev_attrs[0].get(tag):
                    _rcp_emit("SHOW", tag=tag, attrs=attrs[tag])
            _rcp_prev_attrs[0] = attrs
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
                who, tid, loc = pending
                _rcp_emit("SAY", who=who, id=tid, loc=loc)
                _rcp_pending_say[0] = None
        except Exception as e:
            _rcp_emit("ERROR", msg=str(e))

    def _rcp_on_say(event=None, interact=True, **kwargs):
        if not _rcp_enabled[0]:
            return
        if event not in (None, "begin"):
            return
        who = _rcp_get_who()
        # id de traduccion de la linea (PLAN.md D17): el mismo que el compilador VNB guarda por texto
        tid = getattr(renpy.game.context(), "translate_identifier", None) or ""
        loc = _rcp_loc()
        if interact is False:
            _rcp_emit("SAY", who=who, id=tid, loc=loc)
            return
        _rcp_pending_say[0] = (who, tid, loc)

    _rcp_original_display_menu = renpy.exports.display_menu

    def _rcp_display_menu(items, *args, **kwargs):
        if not _rcp_enabled[0]:
            return _rcp_original_display_menu(items, *args, **kwargs)
        _rcp_emit("MENU", loc=_rcp_loc())
        result = _rcp_original_display_menu(items, *args, **kwargs)
        options = []
        for _, value in items:
            vv = getattr(value, "value", value)
            if vv is None:
                continue
            if not getattr(value, "sensitive", True):
                continue
            options.append(vv)
        if result is not None:
            for pos, vv in enumerate(options):
                if result == vv:
                    _rcp_emit("CHOICE", i=pos)
                    break
        return result

    renpy.exports.display_menu = _rcp_display_menu
    renpy.store.menu = _rcp_display_menu

    if _rcp_out_path:
        _rcp_enabled[0] = True
        _dir = _rcp_os.path.dirname(_rcp_out_path)
        if _dir:
            _rcp_os.makedirs(_dir, exist_ok=True)
        _rcp_file[0] = open(_rcp_out_path, "w", encoding="utf-8")

    config.label_callbacks.append(_rcp_on_label)
    config.start_interact_callbacks.append(_rcp_on_interact)
    config.all_character_callbacks.append(_rcp_on_say)
