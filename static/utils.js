export default function importSCSS(scssFileName) {
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
}