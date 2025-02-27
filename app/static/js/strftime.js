(function () {
  function w(e, h, q) {
    function l(g, a, c, f) {
      for (
        var b = "", d = null, r = !1, J = g.length, x = !1, v = 0;
        v < J;
        v++
      ) {
        var n = g.charCodeAt(v);
        if (!0 === r)
          if (45 === n) d = "";
          else if (95 === n) d = " ";
          else if (48 === n) d = "0";
          else if (58 === n)
            x &&
              A(
                "[WARNING] detected use of unsupported %:: or %::: modifiers to strftime"
              ),
              (x = !0);
          else {
            switch (n) {
              case 37:
                b += "%";
                break;
              case 65:
                b += c.days[a.getDay()];
                break;
              case 66:
                b += c.months[a.getMonth()];
                break;
              case 67:
                b += k(Math.floor(a.getFullYear() / 100), d);
                break;
              case 68:
                b += l(c.formats.D, a, c, f);
                break;
              case 70:
                b += l(c.formats.F, a, c, f);
                break;
              case 72:
                b += k(a.getHours(), d);
                break;
              case 73:
                b += k(B(a.getHours()), d);
                break;
              case 76:
                b += C(Math.floor(f % 1e3));
                break;
              case 77:
                b += k(a.getMinutes(), d);
                break;
              case 80:
                b += 12 > a.getHours() ? c.am : c.pm;
                break;
              case 82:
                b += l(c.formats.R, a, c, f);
                break;
              case 83:
                b += k(a.getSeconds(), d);
                break;
              case 84:
                b += l(c.formats.T, a, c, f);
                break;
              case 85:
                b += k(D(a, "sunday"), d);
                break;
              case 87:
                b += k(D(a, "monday"), d);
                break;
              case 88:
                b += l(c.formats.X, a, c, f);
                break;
              case 89:
                b += a.getFullYear();
                break;
              case 90:
                t && 0 === m
                  ? (b += "GMT")
                  : ((d = a.toString().match(/\(([\w\s]+)\)/)),
                    (b += (d && d[1]) || ""));
                break;
              case 97:
                b += c.shortDays[a.getDay()];
                break;
              case 98:
                b += c.shortMonths[a.getMonth()];
                break;
              case 99:
                b += l(c.formats.c, a, c, f);
                break;
              case 100:
                b += k(a.getDate(), d);
                break;
              case 101:
                b += k(a.getDate(), null == d ? " " : d);
                break;
              case 104:
                b += c.shortMonths[a.getMonth()];
                break;
              case 106:
                d = new Date(a.getFullYear(), 0, 1);
                d = Math.ceil((a.getTime() - d.getTime()) / 864e5);
                b += C(d);
                break;
              case 107:
                b += k(a.getHours(), null == d ? " " : d);
                break;
              case 108:
                b += k(B(a.getHours()), null == d ? " " : d);
                break;
              case 109:
                b += k(a.getMonth() + 1, d);
                break;
              case 110:
                b += "\n";
                break;
              case 111:
                d = a.getDate();
                b = c.ordinalSuffixes
                  ? b + (String(d) + (c.ordinalSuffixes[d - 1] || E(d)))
                  : b + (String(d) + E(d));
                break;
              case 112:
                b += 12 > a.getHours() ? c.AM : c.PM;
                break;
              case 114:
                b += l(c.formats.r, a, c, f);
                break;
              case 115:
                b += Math.floor(f / 1e3);
                break;
              case 116:
                b += "\t";
                break;
              case 117:
                d = a.getDay();
                b += 0 === d ? 7 : d;
                break;
              case 118:
                b += l(c.formats.v, a, c, f);
                break;
              case 119:
                b += a.getDay();
                break;
              case 120:
                b += l(c.formats.x, a, c, f);
                break;
              case 121:
                b += k(a.getFullYear() % 100, d);
                break;
              case 122:
                t && 0 === m
                  ? (b += x ? "+00:00" : "+0000")
                  : ((d = 0 !== m ? m / 6e4 : -a.getTimezoneOffset()),
                    (r = x ? ":" : ""),
                    (n = Math.abs(d % 60)),
                    (b +=
                      (0 > d ? "-" : "+") +
                      k(Math.floor(Math.abs(d / 60))) +
                      r +
                      k(n)));
                break;
              default:
                r && (b += "%"), (b += g[v]);
            }
            d = null;
            r = !1;
          }
        else 37 === n ? (r = !0) : (b += g[v]);
      }
      return b;
    }
    var y = e || F,
      m = h || 0,
      t = q || !1,
      u = 0,
      z,
      p = function (g, a) {
        if (a) {
          var c = a.getTime();
          if (t) {
            var f = 6e4 * (a.getTimezoneOffset() || 0);
            a = new Date(c + f + m);
            6e4 * (a.getTimezoneOffset() || 0) !== f &&
              ((a = 6e4 * (a.getTimezoneOffset() || 0)),
              (a = new Date(c + a + m)));
          }
        } else
          (c = Date.now()),
            c > u
              ? ((u = c),
                (z = new Date(u)),
                (c = u),
                t && (z = new Date(u + 6e4 * (z.getTimezoneOffset() || 0) + m)))
              : (c = u),
            (a = z);
        return l(g, a, y, c);
      };
    p.localize = function (g) {
      return new w(g || y, m, t);
    };
    p.localizeByIdentifier = function (g) {
      var a = G[g];
      return a
        ? p.localize(a)
        : (A('[WARNING] No locale found with identifier "' + g + '".'), p);
    };
    p.timezone = function (g) {
      var a = m,
        c = t,
        f = typeof g;
      if ("number" === f || "string" === f)
        (c = !0),
          "string" === f
            ? ((a = "-" === g[0] ? -1 : 1),
              (f = parseInt(g.slice(1, 3), 10)),
              (g = parseInt(g.slice(3, 5), 10)),
              (a = a * (60 * f + g) * 6e4))
            : "number" === f && (a = 6e4 * g);
      return new w(y, a, c);
    };
    p.utc = function () {
      return new w(y, m, !0);
    };
    return p;
  }
  function k(e, h) {
    if ("" === h || 9 < e) return "" + e;
    null == h && (h = "0");
    return h + e;
  }
  function C(e) {
    return 99 < e ? e : 9 < e ? "0" + e : "00" + e;
  }
  function B(e) {
    return 0 === e ? 12 : 12 < e ? e - 12 : e;
  }
  function D(e, h) {
    h = h || "sunday";
    var q = e.getDay();
    "monday" === h && (0 === q ? (q = 6) : q--);
    h = Date.UTC(e.getFullYear(), 0, 1);
    e = Date.UTC(e.getFullYear(), e.getMonth(), e.getDate());
    return Math.floor((Math.floor((e - h) / 864e5) + 7 - q) / 7);
  }
  function E(e) {
    var h = e % 10;
    e %= 100;
    if ((11 <= e && 13 >= e) || 0 === h || 4 <= h) return "th";
    switch (h) {
      case 1:
        return "st";
      case 2:
        return "nd";
      case 3:
        return "rd";
    }
  }
  function A(e) {
    "undefined" !== typeof console &&
      "function" == typeof console.warn &&
      console.warn(e);
  }
  var G = {
      de_DE: {
        identifier: "de-DE",
        days: "Sonntag Montag Dienstag Mittwoch Donnerstag Freitag Samstag".split(
          " "
        ),
        shortDays: "So Mo Di Mi Do Fr Sa".split(" "),
        months:
          "Januar Februar M\u00e4rz April Mai Juni Juli August September Oktober November Dezember".split(
            " "
          ),
        shortMonths:
          "Jan Feb M\u00e4r Apr Mai Jun Jul Aug Sep Okt Nov Dez".split(" "),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d.%m.%Y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      en_CA: {
        identifier: "en-CA",
        days: "Sunday Monday Tuesday Wednesday Thursday Friday Saturday".split(
          " "
        ),
        shortDays: "Sun Mon Tue Wed Thu Fri Sat".split(" "),
        months:
          "January February March April May June July August September October November December".split(
            " "
          ),
        shortMonths: "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(
          " "
        ),
        ordinalSuffixes:
          "st nd rd th th th th th th th th th th th th th th th th th st nd rd th th th th th th th st".split(
            " "
          ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d/%m/%y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%r",
          x: "%D",
        },
      },
      en_US: {
        identifier: "en-US",
        days: "Sunday Monday Tuesday Wednesday Thursday Friday Saturday".split(
          " "
        ),
        shortDays: "Sun Mon Tue Wed Thu Fri Sat".split(" "),
        months:
          "January February March April May June July August September October November December".split(
            " "
          ),
        shortMonths: "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(
          " "
        ),
        ordinalSuffixes:
          "st nd rd th th th th th th th th th th th th th th th th th st nd rd th th th th th th th st".split(
            " "
          ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%m/%d/%y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%r",
          x: "%D",
        },
      },
      es_MX: {
        identifier: "es-MX",
        days: "domingo lunes martes mi\u00e9rcoles jueves viernes s\u00e1bado".split(
          " "
        ),
        shortDays: "dom lun mar mi\u00e9 jue vie s\u00e1b".split(" "),
        months:
          "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(
            " "
          ),
        shortMonths: "ene feb mar abr may jun jul ago sep oct nov dic".split(
          " "
        ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d/%m/%Y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      fr_FR: {
        identifier: "fr-FR",
        days: "dimanche lundi mardi mercredi jeudi vendredi samedi".split(" "),
        shortDays: "dim. lun. mar. mer. jeu. ven. sam.".split(" "),
        months:
          "janvier f\u00e9vrier mars avril mai juin juillet ao\u00fbt septembre octobre novembre d\u00e9cembre".split(
            " "
          ),
        shortMonths:
          "janv. f\u00e9vr. mars avril mai juin juil. ao\u00fbt sept. oct. nov. d\u00e9c.".split(
            " "
          ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d/%m/%Y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      it_IT: {
        identifier: "it-IT",
        days: "domenica luned\u00ec marted\u00ec mercoled\u00ec gioved\u00ec venerd\u00ec sabato".split(
          " "
        ),
        shortDays: "dom lun mar mer gio ven sab".split(" "),
        months:
          "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(
            " "
          ),
        shortMonths: "gen feb mar apr mag giu lug ago set ott nov dic".split(
          " "
        ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d/%m/%Y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      nl_NL: {
        identifier: "nl-NL",
        days: "zondag maandag dinsdag woensdag donderdag vrijdag zaterdag".split(
          " "
        ),
        shortDays: "zo ma di wo do vr za".split(" "),
        months:
          "januari februari maart april mei juni juli augustus september oktober november december".split(
            " "
          ),
        shortMonths: "jan feb mrt apr mei jun jul aug sep okt nov dec".split(
          " "
        ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d-%m-%y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      pt_BR: {
        identifier: "pt-BR",
        days: "domingo segunda ter\u00e7a quarta quinta sexta s\u00e1bado".split(
          " "
        ),
        shortDays: "Dom Seg Ter Qua Qui Sex S\u00e1b".split(" "),
        months:
          "janeiro fevereiro mar\u00e7o abril maio junho julho agosto setembro outubro novembro dezembro".split(
            " "
          ),
        shortMonths: "Jan Fev Mar Abr Mai Jun Jul Ago Set Out Nov Dez".split(
          " "
        ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d-%m-%Y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      ru_RU: {
        identifier: "ru-RU",
        days: "\u0412\u043e\u0441\u043a\u0440\u0435\u0441\u0435\u043d\u044c\u0435 \u041f\u043e\u043d\u0435\u0434\u0435\u043b\u044c\u043d\u0438\u043a \u0412\u0442\u043e\u0440\u043d\u0438\u043a \u0421\u0440\u0435\u0434\u0430 \u0427\u0435\u0442\u0432\u0435\u0440\u0433 \u041f\u044f\u0442\u043d\u0438\u0446\u0430 \u0421\u0443\u0431\u0431\u043e\u0442\u0430".split(
          " "
        ),
        shortDays:
          "\u0412\u0441 \u041f\u043d \u0412\u0442 \u0421\u0440 \u0427\u0442 \u041f\u0442 \u0421\u0431".split(
            " "
          ),
        months:
          "\u042f\u043d\u0432\u0430\u0440\u044c \u0424\u0435\u0432\u0440\u0430\u043b\u044c \u041c\u0430\u0440\u0442 \u0410\u043f\u0440\u0435\u043b\u044c \u041c\u0430\u0439 \u0418\u044e\u043d\u044c \u0418\u044e\u043b\u044c \u0410\u0432\u0433\u0443\u0441\u0442 \u0421\u0435\u043d\u0442\u044f\u0431\u0440\u044c \u041e\u043a\u0442\u044f\u0431\u0440\u044c \u041d\u043e\u044f\u0431\u0440\u044c \u0414\u0435\u043a\u0430\u0431\u0440\u044c".split(
            " "
          ),
        shortMonths:
          "\u044f\u043d\u0432 \u0444\u0435\u0432 \u043c\u0430\u0440 \u0430\u043f\u0440 \u043c\u0430\u0439 \u0438\u044e\u043d \u0438\u044e\u043b \u0430\u0432\u0433 \u0441\u0435\u043d \u043e\u043a\u0442 \u043d\u043e\u044f \u0434\u0435\u043a".split(
            " "
          ),
        AM: "AM",
        PM: "PM",
        am: "am",
        pm: "pm",
        formats: {
          c: "%a %d %b %Y %X",
          D: "%d.%m.%y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      tr_TR: {
        identifier: "tr-TR",
        days: "Pazar Pazartesi Sal\u0131 \u00c7ar\u015famba Per\u015fembe Cuma Cumartesi".split(
          " "
        ),
        shortDays: "Paz Pzt Sal \u00c7r\u015f Pr\u015f Cum Cts".split(" "),
        months:
          "Ocak \u015eubat Mart Nisan May\u0131s Haziran Temmuz A\u011fustos Eyl\u00fcl Ekim Kas\u0131m Aral\u0131k".split(
            " "
          ),
        shortMonths:
          "Oca \u015eub Mar Nis May Haz Tem A\u011fu Eyl Eki Kas Ara".split(
            " "
          ),
        AM: "\u00d6\u00d6",
        PM: "\u00d6S",
        am: "\u00d6\u00d6",
        pm: "\u00d6S",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d-%m-%Y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%T",
          x: "%D",
        },
      },
      zh_CN: {
        identifier: "zh-CN",
        days: "\u661f\u671f\u65e5 \u661f\u671f\u4e00 \u661f\u671f\u4e8c \u661f\u671f\u4e09 \u661f\u671f\u56db \u661f\u671f\u4e94 \u661f\u671f\u516d".split(
          " "
        ),
        shortDays: "\u65e5\u4e00\u4e8c\u4e09\u56db\u4e94\u516d".split(""),
        months:
          "\u4e00\u6708 \u4e8c\u6708 \u4e09\u6708 \u56db\u6708 \u4e94\u6708 \u516d\u6708 \u4e03\u6708 \u516b\u6708 \u4e5d\u6708 \u5341\u6708 \u5341\u4e00\u6708 \u5341\u4e8c\u6708".split(
            " "
          ),
        shortMonths:
          "\u4e00\u6708 \u4e8c\u6708 \u4e09\u6708 \u56db\u6708 \u4e94\u6708 \u516d\u6708 \u4e03\u6708 \u516b\u6708 \u4e5d\u6708 \u5341\u6708 \u5341\u4e00\u6708 \u5341\u4e8c\u6708".split(
            " "
          ),
        AM: "\u4e0a\u5348",
        PM: "\u4e0b\u5348",
        am: "\u4e0a\u5348",
        pm: "\u4e0b\u5348",
        formats: {
          c: "%a %d %b %Y %X %Z",
          D: "%d/%m/%y",
          F: "%Y-%m-%d",
          R: "%H:%M",
          r: "%I:%M:%S %p",
          T: "%H:%M:%S",
          v: "%e-%b-%Y",
          X: "%r",
          x: "%D",
        },
      },
    },
    F = G.en_US,
    H = new w(F, 0, !1);
  if ("undefined" !== typeof module) var I = (module.exports = H);
  else
    (I = (function () {
      return this || (0, eval)("this");
    })()),
      (I.strftime = H);
  "function" !== typeof Date.now &&
    (Date.now = function () {
      return +new Date();
    });
})();
