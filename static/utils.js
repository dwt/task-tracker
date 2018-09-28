export default function importSCSS(scssFileName) {
    importCSS(scssFileName.replace(/\.scss$/, '.css')).addEventListener('error', event => {
        if (!importSCSS.compiler) {
            // REFACT is there a way to express that this depends on 
            // import sassModule from '/static/vendor/sass.js/sass.js'
            // can't use straight import, as sass.js bombs when it has no global object
            if (typeof Sass === 'function') {
                importSCSS.compiler = new Sass()
            }
            else {
                return // just skip sass compilation in the karma runner for now
            }
        }
        fetch(scssFileName)
            .then(response => response.text())
            .then(function (scssString) {
                importSCSS.compiler.compile(scssString, function (css) {
                    let style = document.createElement('style')
                    style.appendChild(document.createTextNode(css.text))
                    document.head.appendChild(style)
                })
    
            })
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