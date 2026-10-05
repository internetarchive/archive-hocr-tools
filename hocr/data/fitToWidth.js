// const pageBase = "001"
// const pageWidth = 3060;
// const pageHeight = 4887;

let browserZoom = null;

function fitToWidth() {
    // fit to width at browserZoom == 100%

    if (window.outerWidth == 0) {
        // this should only happen in document.DOMContentLoaded
        // but not in window.load
        // wait for rendering and try again
        requestAnimationFrame(fitToWidth);
        return;
    }

    const browserZoom2 = Math.round(window.outerWidth / window.innerWidth * 100) / 100;
    if (browserZoom2 == browserZoom) {
        // browserZoom did not change
        return;
    }
    browserZoom = browserZoom2;

    // no, this fails in some cases
    // -1 to account for rounding errors
    // to avoid a horizontal scrollbar on zoom=100%
    // const clientWidth = document.body.clientWidth - 1;

    // no, this breaks on (browserZoom < 1)
    // const clientWidth = document.body.clientWidth;

    const clientWidth = document.documentElement.clientWidth;

    // scale the page element
    const scale = clientWidth / pageWidth * browserZoom;

    // horizontally center the page element
    const left = Math.max(0, Math.round((clientWidth - pageWidth * scale) / 2));

    // scale the page element
    const page = document.getElementById(`page-${pageBase}`);
    // page.style.transformOrigin = "top left";
    // no, this breaks the horizontal centering of the page
    // fix: move left to page.style.marginLeft
    // page.style.transform = `translateX(${left}px) scale(${scale})`;
    page.style.transform = `scale(${scale})`;

    // center the page element
    page.style.marginLeft = `${left}px`;

    // scale the body height
    // to remove extra margin below the page
    document.body.style.height = `${pageHeight * scale}px`;

    if (browserZoom <= 1) {
        // avoid a horizontal scrollbar on zoom=100%
        document.body.style.overflowX = "hidden";
    }
    else {
        document.body.style.overflowX = "auto";
    }

    const pageBbox = page.getBoundingClientRect();
    console.log(
        `fitToWidth:`,
        `pageWidth=${pageWidth}`,
        `outerWidth=${window.outerWidth}`,
        `innerWidth=${window.innerWidth}`,
        `clientWidth=${clientWidth}`,
        `htmlClientWidth=${document.documentElement.clientWidth}`,
        `htmlScrollWidth=${document.documentElement.scrollWidth}`,
        `htmlBboxWidth=${document.documentElement.getBoundingClientRect().width}`,
        `bodyClientWidth=${document.body.clientWidth}`,
        `bodyScrollWidth=${document.body.scrollWidth}`,
        `bodyBboxWidth=${document.body.getBoundingClientRect().width}`,
        `pageOffsetWidth=${page.offsetWidth}`,
        `pageBbox=[${pageBbox.x}, ${pageBbox.y}, ${pageBbox.width}, ${pageBbox.height}]`,
        `browserZoom=${browserZoom}`,
        `scale=${scale}`,
        `left=${left}`
    );

    if (false) {
        // debug: find elements that overflow the page element
        // fixed by adding: div.page { overflow: hidden; }
        const htmlClientWidth = document.documentElement.clientWidth;
        for (const e of document.querySelectorAll("*")) {
            const r = e.getBoundingClientRect();
            if (r.right > htmlClientWidth + 1) {
                console.log("overflow element:", e, r.right);
            }
        }

    }
}

// window.addEventListener("load", fitToWidth);
// window.addEventListener("resize", fitToWidth);
