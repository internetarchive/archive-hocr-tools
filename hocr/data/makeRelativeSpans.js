function makeRelativeSpans(joinLines=1, addSoftHyphens=1) {

  // convert span elements from position:absolute to position:relative
  // to enable text search across words

  // let joinLines = 0;

  // join lines of a paragraph to enable text search across lines
  // also join hyphenated words
  // FIXME this breaks in tor-browser
  // because fontWidthRel is not constant with font-family:monospace
  // let joinLines = 1;

  // only for joinLines = 1
  // let addSoftHyphens = 1;

  // FIXME get the actual relative font width = width/height
  let fontWidthRel = 0.6;

  let _parseFloat = parseFloat; // help minify

  let _textContentAttr = "textContent"; // help minify

  // loop containers
  for (let container of document.querySelectorAll("div.p")) {

    let containerStyle = container.style; // help minify

    let cursorX = 0;
    let cursorY = 0;

    // this was position:relative to allow absolute-positioned spans
    containerStyle.position = "absolute";

    // dont break too-long lines
    containerStyle.whiteSpace = "nowrap";

    let containerFontSize = _parseFloat(containerStyle.fontSize || 16);

    let spaceWidth = containerFontSize * fontWidthRel;

    let containerX = _parseFloat(containerStyle.left || 0);
    let containerY = _parseFloat(containerStyle.top || 0);

    let spans = container.querySelectorAll("span");
    let lastSpanIdx = spans.length - 1;

    // loop spans
    for (let spanIdx = 0; spanIdx < spans.length; spanIdx++) {

      let span = spans[spanIdx];
      let nextSpan = spans[spanIdx + 1];

      if (span == null) {
        continue;
      }

      let spanIsBreak = span.innerHTML.startsWith("<br");
      let nextSpanIsBreak = nextSpan?.innerHTML.startsWith("<br");

      let spanStyle = span.style; // help minify

      let x = _parseFloat(spanStyle.left || 0) - containerX;
      let y = _parseFloat(spanStyle.top || 0) - containerY;

      let fontSize = _parseFloat(spanStyle.fontSize || 16);

      // example: scaleX(0.9)
      let scaleMatch = spanStyle.transform?.match(/scaleX\(([^)]+)\)/);
      let scaleX = scaleMatch ? _parseFloat(scaleMatch[1]) : 1;

      let spanTextLength = span[_textContentAttr].length;
      if (span[_textContentAttr].endsWith("\xa0")) {
        // remove trailing &nbsp;
        span[_textContentAttr] = span[_textContentAttr].slice(0, -1);
        spanTextLength--;
      }

      let todoDecreaseCursorX = 0;

      if (nextSpanIsBreak && spanIdx < (lastSpanIdx - 1) && joinLines) {
        let nextNextSpan = spans[spanIdx + 2];
        if (span[_textContentAttr].endsWith("-") && span[_textContentAttr].slice(-2, -1) != " ") {
          // join hyphenated word
          // NOTE this can be lossy if the hyphen at end of line is a "hard hyphen"
          // in expressions like "state-of-the-art" or "visit-my-page.com"
          // best we can do is to replace the hyphen with a soft hyphen (&shy;)
          let nextNextSpanText = nextNextSpan[_textContentAttr];
          if (nextNextSpanText.endsWith("\xa0")) {
            // remove trailing &nbsp;
            nextNextSpanText = nextNextSpanText.slice(0, -1);
          }

          // soft hyphen = \xAD = 0xC2 0xAD in utf8 = &#173; in XHTML = &shy; in HTML
          // https://unicodeplus.com/U+00AD
          span[_textContentAttr] = (
            span[_textContentAttr].slice(0, -1) // remove the trailing hyphen
            // + "&#173;" // add soft hyphen
            + (addSoftHyphens ? "\xAD" : "") // add soft hyphen
            + nextNextSpanText // add second half of the word
          );
          spanTextLength = (
            spanTextLength
            - 1 // remove the trailing hyphen
            + nextNextSpanText.length // add second half of the word
          );
          let hyphenWidth = fontSize * fontWidthRel * 1;
          let nextNextFontSize = _parseFloat(nextNextSpan.style.fontSize || 16);

          let nextNextScaleMatch = nextNextSpan.style.transform?.match(/scaleX\(([^)]+)\)/);
          let nextNextScaleX = nextNextScaleMatch ? _parseFloat(nextNextScaleMatch[1]) : 1;
          todoDecreaseCursorX = (nextNextFontSize * fontWidthRel * nextNextSpanText.length * nextNextScaleX) + spaceWidth

          nextNextSpan.remove(); // remove nextNextSpan from container
          spans[spanIdx + 2] = null; // remove nextNextSpan from spans
        }
      }

      let bboxWidth = fontSize * fontWidthRel * spanTextLength;
      let scaledBboxWidth = bboxWidth * scaleX;

      // transform:scaleX has no effect with display:inline
      // so we have to translate scaleX to letterSpacing
      // fontSize = fontSize * scaleX;
      // spanStyle.fontSize = fontSize + "px";
      let letterSpacing = (scaledBboxWidth - bboxWidth) / spanTextLength;
      spanStyle.letterSpacing = letterSpacing + "px";

      let dx = x - cursorX;
      let dy = y - cursorY;

      spanStyle.position = "relative";

      // fix: text is shifted down
      spanStyle.verticalAlign = "top";

      // no, display:inline-block breaks text search
      // spanStyle.display = "inline-block";
      // display:inline disables spanStyle.transform
      spanStyle.display = "inline";

      // apply cursor delta
      spanStyle.left = dx + "px";
      spanStyle.top = dy + "px";

      cursorX += scaledBboxWidth + spaceWidth;

      if (todoDecreaseCursorX) {
        cursorX -= todoDecreaseCursorX;
        // cursorX += todoDecreaseCursorX;
        todoDecreaseCursorX = 0;
      }

      if (spanIsBreak && spanIdx < lastSpanIdx) {
        if (!joinLines) {
          cursorX = 0;
          cursorY += fontSize;
        }
        else {
          span.remove();
        }
      }
    } // loop spans
  } // loop containers
}
