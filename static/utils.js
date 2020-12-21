export function importSCSS(scssFileName) {
    importCSS(scssFileName.replace(/\.scss$/, '.css')).addEventListener('error', event => {
        fetch(scssFileName)
            .then(response => response.text())
            .then(compileAndActivate)
    })
}

// use this as a template tag scss`some multiline scss string`
export function scss(scssText) {
	compileAndActivate(String.raw(scssText))
}

function compileAndActivate(scssString) {
    if (!compileAndActivate.compiler) {
        // REFACT is there a way to express that this depends on 
        // import sassModule from '/static/vendor/sass.js/sass.js'
        // can't use straight import, as sass.js bombs when it has no global object
        if (typeof Sass === 'function') {
            compileAndActivate.compiler = new Sass()
        }
        else {
            return // just skip sass compilation in the karma runner for now
        }
    }
    
    compileAndActivate.compiler.compile(scssString, function (css) {
        let style = document.createElement('style')
        style.appendChild(document.createTextNode(css.text))
        document.head.appendChild(style)
    })
}

export function importCSS(cssFileName) {
    let link = document.createElement('link')
    link.href = cssFileName
    link.rel = 'stylesheet'
    document.head.appendChild(link)
    return link
    // fetch(cssFileName)
    //     .then(response => response.text())
    //     .then(function (cssString) {
    //         let style = document.createElement('style')
    //         style.appendChild(document.createTextNode(cssString))
    //         document.head.appendChild(style)
    //     })
}

export function vueTemplate(templateString) {
    return String.raw(templateString)
}

// TODO build a function that 
// 1) compiles scss and inserts it into the dom
// 2) compiles templates and inserts them into the dom or attaches them to a vue object
// 3) prepares and exports a vue object
// All in all, this should give the feeling (and provide the highlighter with enough clues so it can highlight) of a .vue file that contains styles, templates and code for a module
