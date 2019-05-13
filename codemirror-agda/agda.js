// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

(function(mod) {
  if (typeof exports == "object" && typeof module == "object") // CommonJS
    mod(require("../../lib/codemirror"));
  else if (typeof define == "function" && define.amd) // AMD
    define(["../../lib/codemirror"], mod);
  else // Plain browser env
    mod(CodeMirror);
})(function(CodeMirror) {
"use strict";

CodeMirror.defineMode("agda", function(_config, modeConfig) {

  function switchState(source, setState, f) {
    setState(f);
    return f(source, setState);
  }

  // from Haskell-mode
  // These should all be Unicode extended, as per the Haskell 2010 report
  var smallRE = /[a-z_]/;
  var largeRE = /[A-Z]/;
  var digitRE = /\d/;
  var hexitRE = /[0-9A-Fa-f]/;
  var octitRE = /[0-7]/;
  var idRE = /[a-z_A-Z0-9'\xa1-\uffff\[\],]/;
  var symbolRE = /[-!#$%&*+.\/<=>?@\\^|~:]/;
  var specialRE = /[.();@{}]/;
  // ".", ";", "{", "}", "(", ")", "\"", "@")
  var whiteCharRE = /[ \t\v\f]/; // newlines are handled in tokenizer

  /*
  // from agda-mode (UNUSED)
  //  ========================================================================================
  const floatRegex = /-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?(?=[.;{}()@"\s]|$)/u;
  const integerRegex = /-?(?:0|[1-9]\d*|0x[0-9A-Fa-f]+)(?=[.;{}()@"\s]|$)/u;

  const keywordsRegex = new RegExp(
    "(?:[_=|→:?\\\\λ∀]|->|\\.{2,3}|abstract|as|codata|coinductive|constructor|" +
      "data|do|eta-equality|field|forall|hiding|import|in|inductive|" +
      "infix|infixl|infixr|instance|let|macro|module|mutual|no-eta-equality|" +
      "open|overlap|pattern|postulate|primitive|private|public|quote|" +
      "quoteContext|quoteGoal|quoteTerm|record|renaming|rewrite|" +
      "syntax|tactic|to|unquote|unquoteDecl|unquoteDef|using|variable|where|with|" +
      'Set(?:\\d+|[₀₁₂₃₄₅₆₇₈₉]+)?)(?=[.;{}()@"\\s]|$)',
    "u"
  );

  const escapeDec = "0|[1-9]\\d*";
  const escapeHex = "x(?:0|[1-9A-Fa-f][0-9A-Fa-f]*)";
  const escapeCode =
    "[abtnvf&\\\\'\"]|NUL|SOH|STX|ETX|EOT|ENQ|ACK|BEL|BS|HT|LF|VT|FF|CR|" +
    "SO|SI|DLE|DC[1-4]|NAK|SYN|ETB|CAN|EM|SUB|ESC|FS|GS|RS|US|SP|DEL";
  const escapeChar = new RegExp(
    "\\\\(?:" + escapeDec + "|" + escapeHex + "|" + escapeCode + ")",
    "u"
  );
  //  ========================================================================================
  */

  function normal(source, setState) {
    if (source.eatWhile(whiteCharRE)) {
      return null;
    }

    var ch = source.next();
    if (specialRE.test(ch)) {
      if (ch == '{' && source.eat('-')) {
        var t = "comment";
        if (source.eat('#')) {
          t = "meta";
        }
        return switchState(source, setState, ncomment(t, 1));
      }
      return null;
    }

    if (ch == '\'') {
      if (source.eat('\\')) {
        source.next();  // should handle other escapes here
      }
      else {
        source.next();
      }
      if (source.eat('\'')) {
        return "string";
      }
      return "string error";
    }

    if (ch == '"') {
      return switchState(source, setState, stringLiteral);
    }

    if (idRE.test(ch)) {
      source.eatWhile(idRE);
      if (source.eat('.')) {
        return "qualifier";
      }
      return "variable";
    }

    if (digitRE.test(ch)) {
      if (ch == '0') {
        if (source.eat(/[xX]/)) {
          source.eatWhile(hexitRE); // should require at least 1
          return "integer";
        }
        if (source.eat(/[oO]/)) {
          source.eatWhile(octitRE); // should require at least 1
          return "number";
        }
      }
      source.eatWhile(digitRE);
      var t = "number";
      if (source.match(/^\.\d+/)) {
        t = "number";
      }
      if (source.eat(/[eE]/)) {
        t = "number";
        source.eat(/[-+]/);
        source.eatWhile(digitRE); // should require at least 1
      }
      return t;
    }

    if (ch == "." && source.eat("."))
      return "keyword";

    if (symbolRE.test(ch)) {
      if (ch == '-' && source.eat(/-/)) {
        source.eatWhile(/-/);
        if (!source.eat(symbolRE)) {
          source.skipToEnd();
          return "comment";
        }
      }
      var t = "variable";
      if (ch == ':') {
        t = "variable-2";
      }
      source.eatWhile(symbolRE);
      return t;
    }

    return "error";
  }

  function ncomment(type, nest) {
    if (nest == 0) {
      return normal;
    }
    return function(source, setState) {
      var currNest = nest;
      while (!source.eol()) {
        var ch = source.next();
        if (ch == '{' && source.eat('-')) {
          ++currNest;
        }
        else if (ch == '-' && source.eat('}')) {
          --currNest;
          if (currNest == 0) {
            setState(normal);
            return type;
          }
        }
      }
      setState(ncomment(type, currNest));
      return type;
    };
  }

  function stringLiteral(source, setState) {
    while (!source.eol()) {
      var ch = source.next();
      if (ch == '"') {
        setState(normal);
        return "string";
      }
      if (ch == '\\') {
        if (source.eol() || source.eat(whiteCharRE)) {
          setState(stringGap);
          return "string";
        }
        if (source.eat('&')) {
        }
        else {
          source.next(); // should handle other escapes here
        }
      }
    }
    setState(normal);
    return "string error";
  }

  function stringGap(source, setState) {
    if (source.eat('\\')) {
      return switchState(source, setState, stringLiteral);
    }
    source.next();
    setState(normal);
    return "error";
  }

  var wellKnownWords = (function() {
    var wkw = {};
    function setType(t) {
      return function () {
        for (var i = 0; i < arguments.length; i++)
          wkw[arguments[i]] = t;
      };
    }

    // reserved keywords
    // those appear in bold green
    setType("keyword")(
      "abstract", /*"as",*/ "codata", "coinductive", "constructor", "data", "do", "eta-equality",
      "field", "forall", "hiding", "import", "in", "inductive", "infix", "infixl", "infixr", "instance",
      "let", "macro", "module", "mutual", "no-eta-equality", "open", "overlap",
      "pattern", "postulate", "primitive", "private", "public", "quote", "quoteContext", "quoteGoal", "quoteTerm",
      "record", "renaming", "rewrite", "syntax", "tactic", "unquote", "unquoteDecl", "unquoteDef", "using", "where", "with");

    // setType("builtin")(".", ";", "{", "}", "(", ")", "\"", "@");

    // builtin symbols
    // those appear in green
    setType("builtin")(
      "Set", "Set1", "Set2", "{", "}", "=", "|", "->", "→", ":", "?", "\\", "λ", "∀", "..", "...", "(", ")");

    var override = modeConfig.overrideKeywords;
    if (override) for (var word in override) if (override.hasOwnProperty(word))
      wkw[word] = override[word];

    return wkw;
  })();

  return {
    startState: function ()  { return { f: normal }; },
    copyState:  function (s) { return { f: s.f }; },

    token: function(stream, state) {
      var t = state.f(stream, function(s) { state.f = s; });
      var w = stream.current();
      return wellKnownWords.hasOwnProperty(w) ? wellKnownWords[w] : t;
    },

    blockCommentStart: "{-",
    blockCommentEnd: "-}",
    lineComment: "--"
  };

});

CodeMirror.defineMIME("text/x-agda", "agda");
CodeMirror.defineMIME("text/agda", "agda");

});