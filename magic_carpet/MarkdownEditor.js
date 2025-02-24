// MarkdownEditor.js
import React, { useEffect, useRef } from "react";

export default function MarkdownEditor({ initialMarkdown, onChange }) {
    const textareaRef = useRef(null);
    const editorRef = useRef(null);

    useEffect(() => {
        const computeInitialValue = () => {
            if (Array.isArray(initialMarkdown)) {
                return initialMarkdown.join("\n");
            }
            if (typeof initialMarkdown === "string") {
                return initialMarkdown;
            }
            return "";
        };

        const initialValue = computeInitialValue();
        // global EasyMDE from <script> in index.html
        editorRef.current = new EasyMDE({
            element: textareaRef.current,
            initialValue,
            autoDownloadFontAwesome: false,
            spellChecker: false,
            status: [
                "autosave",
                {
                    className: "md-line-count",
                    defaultValue: (el) => {
                        el.innerHTML = "0 lines";
                    },
                    onUpdate: (el) => {
                        if (editorRef.current) {
                            const lineCount = editorRef.current.codemirror.lineCount();
                            el.innerHTML = lineCount + (lineCount === 1 ? " line" : " lines");
                        }
                    },
                },
                {
                    className: "md-word-count",
                    defaultValue: (el) => {
                        el.innerHTML = "0 words";
                    },
                    onUpdate: (el) => {
                        if (editorRef.current) {
                            const str = editorRef.current.codemirror.getValue();
                            const wordCount = (str.match(/\S+/g) || []).length;
                            el.innerHTML = wordCount + (wordCount === 1 ? " word" : " words");
                        }
                    },
                },
            ],
            autoSave: {
                enabled: true,
                delay: 1000,
                uniqueId: "editorAutosave",
            },
            renderingConfig: {
                singleLineBreaks: false,
                codeSyntaxHighlighting: true,
            },
            toolbar: [
                "bold",
                "italic",
                "unordered-list",
                "ordered-list",
                "preview",
                "fullscreen",
                "guide",
            ],
        });

        editorRef.current.codemirror.on("change", () => {
            const value = editorRef.current.value();
            onChange(value);
        });

        return () => {
            if (editorRef.current) {
                editorRef.current.toTextArea();
                editorRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        if (editorRef.current) {
            let newVal = "";
            if (Array.isArray(initialMarkdown)) {
                newVal = initialMarkdown.join("\n");
            } else if (typeof initialMarkdown === "string") {
                newVal = initialMarkdown;
            }
            if (editorRef.current.value() !== newVal) {
                editorRef.current.value(newVal);
            }
        }
    }, [initialMarkdown]);

    return (
        <div className="EasyMDEContainer">
            <textarea ref={textareaRef} />
        </div>
    );
}