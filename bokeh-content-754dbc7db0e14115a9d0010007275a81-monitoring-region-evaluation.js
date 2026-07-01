(function() {
  const fn = function() {
    'use strict';
    (function(root) {
      function now() {
        return new Date();
      }
    
      const force = false;
    
      if (typeof root._bokeh_onload_callbacks === "undefined" || force === true) {
        root._bokeh_onload_callbacks = [];
        root._bokeh_is_loading = undefined;
      }
    
    
    const element = document.getElementById("cea58a3e-512e-47d0-9f09-166f695368e5");
        if (element == null) {
          console.warn("Bokeh: autoload.js configured with elementid 'cea58a3e-512e-47d0-9f09-166f695368e5' but no matching script tag was found.")
        }
      function run_callbacks() {
        try {
          root._bokeh_onload_callbacks.forEach(function(callback) {
            if (callback != null)
              callback();
          });
        } finally {
          delete root._bokeh_onload_callbacks
        }
        console.debug("Bokeh: all callbacks have finished");
      }
    
      function load_libs(css_urls, js_urls, callback) {
        if (css_urls == null) css_urls = [];
        if (js_urls == null) js_urls = [];
    
        root._bokeh_onload_callbacks.push(callback);
        if (root._bokeh_is_loading > 0) {
          console.debug("Bokeh: BokehJS is being loaded, scheduling callback at", now());
          return null;
        }
        if (js_urls == null || js_urls.length === 0) {
          run_callbacks();
          return null;
        }
        console.debug("Bokeh: BokehJS not loaded, scheduling load and callback at", now());
        root._bokeh_is_loading = css_urls.length + js_urls.length;
    
        function on_load() {
          root._bokeh_is_loading--;
          if (root._bokeh_is_loading === 0) {
            console.debug("Bokeh: all BokehJS libraries/stylesheets loaded");
            run_callbacks()
          }
        }
    
        function on_error(url) {
          console.error("failed to load " + url);
        }
    
        for (let i = 0; i < css_urls.length; i++) {
          const url = css_urls[i];
          const element = document.createElement("link");
          element.onload = on_load;
          element.onerror = on_error.bind(null, url);
          element.rel = "stylesheet";
          element.type = "text/css";
          element.href = url;
          console.debug("Bokeh: injecting link tag for BokehJS stylesheet: ", url);
          document.body.appendChild(element);
        }
    
        for (let i = 0; i < js_urls.length; i++) {
          const url = js_urls[i];
          const element = document.createElement('script');
          element.onload = on_load;
          element.onerror = on_error.bind(null, url);
          element.async = false;
          element.src = url;
          console.debug("Bokeh: injecting script tag for BokehJS library: ", url);
          document.head.appendChild(element);
        }
      };
    
      function inject_raw_css(css) {
        const element = document.createElement("style");
        element.appendChild(document.createTextNode(css));
        document.body.appendChild(element);
      }
    
      const js_urls = ["https://cdn.bokeh.org/bokeh/release/bokeh-3.9.0.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-gl-3.9.0.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.9.0.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-tables-3.9.0.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-mathjax-3.9.0.min.js"];
      const css_urls = [];
    
      const inline_js = [    function(Bokeh) {
          Bokeh.set_log_level("info");
        },
        function(Bokeh) {
          (function() {
            const fn = function() {
              Bokeh.safely(function() {
                (function(root) {
                  function embed_document(root) {
                  const docs_json = '{"ea539a7a-db02-4e72-ae44-0497d0eb4085":{"version":"3.9.0","title":"Bokeh Application","config":{"type":"object","name":"DocumentConfig","id":"p1332","attributes":{"notifications":{"type":"object","name":"Notifications","id":"p1333"}}},"roots":[{"type":"object","name":"Figure","id":"p1334","attributes":{"width":700,"height":320,"x_range":{"type":"object","name":"DataRange1d","id":"p1335"},"y_range":{"type":"object","name":"DataRange1d","id":"p1336"},"x_scale":{"type":"object","name":"LinearScale","id":"p1343"},"y_scale":{"type":"object","name":"LinearScale","id":"p1344"},"title":{"type":"object","name":"Title","id":"p1341","attributes":{"text":"Category context CDF: best-donor minima vs training station-pairs"}},"renderers":[{"type":"object","name":"GlyphRenderer","id":"p1365","attributes":{"data_source":{"type":"object","name":"ColumnDataSource","id":"p1359","attributes":{"selected":{"type":"object","name":"Selection","id":"p1360","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1361"},"data":{"type":"map","entries":[["x",{"type":"ndarray","array":{"type":"bytes","data":"H4sIAAEAAAAA/yWUeTiVaRjGlURlKqpLhYTSoLQ3TdttL6MkY6QQEzWjHJkW4VBKm0pZ0jZNXCEqySglRcTVRZvIcjic5Tv76qAkS815v/nrvt7nW577/T2Ljo6OY++6aujo6My2CX6L8RsGPK7yGsjZsW1GI3wcX+4zH9NEzok/lDehpGMwwGDbR3zvrzp1WvORnNnWR5sRfH1lBDXcjNZW7jevAy2o9WesXchpwRXzhjtM91bkp482bitqxY60r8bR09tw7/6LkYUxbSSeXvO+DZ26phU1c1l0PmcmC1Z9ebLm9yzst5SLc6zakXPYbey2g+3YQy3qL69qJ36yVfodcBd7Tunf3IGgM+U/z7/agRp/RtCerg7yvGrMbDbG4elklzA2zF7t2Tt8h43us28PP1OwcX3l+cxr8zvR0spdlxnZCdnuDz5HCzvh3PzOcYGqEw6uXRvdFnQhPpyKCo7sQn+V+6TFRVp9oh+dpO6CX8DR1dZ2HJInZCCMA705w65vszkYUR1TGbVzMFB/0uDAZC7q48N3DrhzEXimPJYdz4XWrqSkhEvzXCzi4nxLK6INeTjKDAnNt+Fp3R6aYuXEw5r8dCohkIcTWYEFvtE8LPILCLZP5RFfhgl36Xjdmloe2Fr8JhweFvsFcC9/4eH0vx0zDY34+FRUN/zUlo+lf7Y3Slz4mPlIWaYJ4qNqbXGaXgwfGwbqRbI0PsmfNXyXD6+5eq6MWj59H1bX//r8C63ZlUYUEsIp7+z5FO27153Clp+S+mt+p5CqyfB8zKRQpr+ig5tJIYUzLbbuAYVq9+7xAfUUwiqX/eVNUfBnjKRED1Goiw93Pj9NQOKNqxYJ4O3gmpDoIYDE18dxVagAN5zeRA7GC8AYUY0af1mAtcWNq1kPBITHS/5rAanXTXOxgPZZPUpI3nMaMhNC5NzM0F0pxCazV68VPkL05SUnfWQICW/9pGQhONOubRbmCnE7uebq5iohhti6zP0dQsLNouKTkPRrRcFEEakfw8BWRPrlnIWLCBYs6T+jd4iwNazyUkasiOTZtOOSCKsyp6aWFokw2vjI/lV1IriJPfvSKBEStYWxHBHRdU+dLgZLGpR2cakYby5IfEO9xHj8rT+REy6mef5yUozZ/Hlt4dlieGt5Li8X03xNWmidXawWQxnjtWu7gQT7JkU8CrKSkLjjljW0Jrb9JqHvFR8lQdzWMI7DOQkiRlR889sSHLSzDQmulpB699h1SvBQGaPW/yIh9f6+0ViKohdro2wXSDE1VfNQsF6K4rr45Oc7pWh8ZpURmyCFaYW98dtrUnwoEXytLpVio5brwiYpBptqj7l0S1Hwt9Pe44Yy4qMqzFZGz32Eu4xwF+SFyVA+45FyepIMOZFj75ffkmHjlNNpsTUy3PzVw3K7QAbdOcO5W0bLIdTynGgtJ/1s0OMihxlLOtK3S07fP/UUrY7H8+WImn6Pwa2Xo/DxN78GpRxJWYE/tkxSQLs23ugvU0B9LKUy11+B1xckBxuYCpK/MDBLgeMpnNJvNQrYmNwqui9V0P1Ya6jEWS2HiCVKMh9pN/yV+ONDifXYI0q8vmJTlJGnRNSkiGV675RkTyxP/6zEiritueGzVGCG5DyZt15F5uz6pSgVmT9d5nUVEvdbni2oVSHGa67bs14VmbcBo1lqsj9S2Z5qVNgvebE6To3Wd9mi1YVqDBngqZpSkz6bUG7WDY9R4yyE22mFzs1udBpu788UdxNfoRNNNeR7fHfT4LJ5Q/LQIQ0mhpZmRt7TgD2LtcFUpKH3aZ9ND8pmPIqQRfbARm+O2Z2XPYSfTo91L44wQ6wtL/YiTuvnxuQ+mMt3F9/O6oO9ya3InW6fkJTCORRt+hnVmx1OlI18Rit3ln9tTz/EeckuTr4DKI0Pv/XRaRCDVe4L7SRD5L8hE3zHOv4H8CYggkAGAAA="},"shape":[200],"dtype":"float64","order":"little"}],["y",{"type":"ndarray","array":{"type":"bytes","data":"H4sIAAEAAAAA/y2Vd2yNURjGjdhCUxqEWLF3kCLIY8cWI4gSxAhixBZb1Axii9VSxBaqVFWpFlWt6ri9ve1te/deagVBfOe9z/3n5tzzfed93uf5vedWqxb+LM1PtA06swHh71hcGHikWG86xvVp7I6Nn3vw+Xn+Hoc5m4bcPFkjgfvXsb5b17aWzjf53G0crYw633vSPT7/ANPHVa+HlId8LxELrm0e7ZzwmO8nYdXfwJ6jlU94TjK2zlr8sv/aZzwvBfsflf021kzluS9wqsHUAXvPpvH8lxD5TdNZJx16U2uDe95r1stARUOlOIN1M6GePv45k/XfwCONv6WOt6iSAu+oJws/0seEDudmUdd7iNyobOrLRs2Wad37zv9AnTmoP/Zn9r5bOdSbi8Yb+y0rrcql7o9olrC6ds/BedSfh1afbl/fHfuJfeQjcue6dt6l+ewnH6c1tacaFLCvAjS/e//V0IcF7K8QF4fnHHPNKGSfhWijdX/iVyH7LcJVVS6uiH0XoWOtDn/sI3TsX4dbcoCOPhSjR9/5CgH6UYwH77cvt/bR0xc9wtt6+lOCpO/JdaK3ltCnEgg+rQ30y4DU9l9vHMo00LdSICVCOUL/SvF6Sq9RFQ3L6GMZNDiaHHhURj+NkPIzjfTViIlq97eR/pYjT9kXX06fyzFtWIY6kX5XQCdAVND3SswOA0f/K2GUAE3MwQTpXm9iHmasFcPNzMWMxwKQmfmY8U0MMjMnC6IFYAvzskDR3uSAhblZ2L6F+Vmhwa0JsDJHK9R0Re60Mk8rdggOVuZqhQo/tb2N+dqgpitio4052zBS9/HKkiwb87ZBxreFnbnb8W6Fb03jlXbmb0ddEWwnB3bIuEY4yIMDh3PPdWq0yEEuHJDlEwf5cEBbaAQ4yYkTEuccJ3lxQmPxzcJ7TnLjhFo9/eckPy4I3lNd5MiFmTG7ti245iJPLki57y5y5Yah6tL4+mPd5MsNGb8LbnLmhuo2ye8mbx5clgvIQ+48kOvhhIf8eaDcTbR5yKEX0k60lzx6oeiae9BLLr1wCJ5e8ulDFxloHzn1QdEas8tHXn24I+PqI7c++LdM1kbQT379ELs2+cmxH1o4GlJ+8uyHXH8tA+Q6gC/aNM1eFSDfAfQXQAPkPAC5niOD5D0INZ2zFgfJfRA/JYAg+Q9icJwyKMQ5CEHGLSbEeQghTQqEOBchhP81PuM/0iiBeUAGAAA="},"shape":[200],"dtype":"float64","order":"little"}]]}}},"view":{"type":"object","name":"CDSView","id":"p1366","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1367"}}},"glyph":{"type":"object","name":"Line","id":"p1362","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"#8b005d","line_width":2.8}},"nonselection_glyph":{"type":"object","name":"Line","id":"p1363","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"#8b005d","line_alpha":0.1,"line_width":2.8}},"muted_glyph":{"type":"object","name":"Line","id":"p1364","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"#8b005d","line_alpha":0.2,"line_width":2.8}}}},{"type":"object","name":"GlyphRenderer","id":"p1376","attributes":{"data_source":{"type":"object","name":"ColumnDataSource","id":"p1370","attributes":{"selected":{"type":"object","name":"Selection","id":"p1371","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1372"},"data":{"type":"map","entries":[["x",{"type":"ndarray","array":{"type":"bytes","data":"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"},"shape":[200],"dtype":"float64","order":"little"}],["y",{"type":"ndarray","array":{"type":"bytes","data":"H4sIAAEAAAAA/y2Vd2yNURjGjdhCUxqEWLF3kCLIY8cWI4gSxAhixBZb1Axii9VSxBaqVFWpFlWt6ri9ve1te/deagVBfOe9z/3n5tzzfed93uf5vedWqxb+LM1PtA06swHh71hcGHikWG86xvVp7I6Nn3vw+Xn+Hoc5m4bcPFkjgfvXsb5b17aWzjf53G0crYw633vSPT7/ANPHVa+HlId8LxELrm0e7ZzwmO8nYdXfwJ6jlU94TjK2zlr8sv/aZzwvBfsflf021kzluS9wqsHUAXvPpvH8lxD5TdNZJx16U2uDe95r1stARUOlOIN1M6GePv45k/XfwCONv6WOt6iSAu+oJws/0seEDudmUdd7iNyobOrLRs2Wad37zv9AnTmoP/Zn9r5bOdSbi8Yb+y0rrcql7o9olrC6ds/BedSfh1afbl/fHfuJfeQjcue6dt6l+ewnH6c1tacaFLCvAjS/e//V0IcF7K8QF4fnHHPNKGSfhWijdX/iVyH7LcJVVS6uiH0XoWOtDn/sI3TsX4dbcoCOPhSjR9/5CgH6UYwH77cvt/bR0xc9wtt6+lOCpO/JdaK3ltCnEgg+rQ30y4DU9l9vHMo00LdSICVCOUL/SvF6Sq9RFQ3L6GMZNDiaHHhURj+NkPIzjfTViIlq97eR/pYjT9kXX06fyzFtWIY6kX5XQCdAVND3SswOA0f/K2GUAE3MwQTpXm9iHmasFcPNzMWMxwKQmfmY8U0MMjMnC6IFYAvzskDR3uSAhblZ2L6F+Vmhwa0JsDJHK9R0Re60Mk8rdggOVuZqhQo/tb2N+dqgpitio4052zBS9/HKkiwb87ZBxreFnbnb8W6Fb03jlXbmb0ddEWwnB3bIuEY4yIMDh3PPdWq0yEEuHJDlEwf5cEBbaAQ4yYkTEuccJ3lxQmPxzcJ7TnLjhFo9/eckPy4I3lNd5MiFmTG7ti245iJPLki57y5y5Yah6tL4+mPd5MsNGb8LbnLmhuo2ye8mbx5clgvIQ+48kOvhhIf8eaDcTbR5yKEX0k60lzx6oeiae9BLLr1wCJ5e8ulDFxloHzn1QdEas8tHXn24I+PqI7c++LdM1kbQT379ELs2+cmxH1o4GlJ+8uyHXH8tA+Q6gC/aNM1eFSDfAfQXQAPkPAC5niOD5D0INZ2zFgfJfRA/JYAg+Q9icJwyKMQ5CEHGLSbEeQghTQqEOBchhP81PuM/0iiBeUAGAAA="},"shape":[200],"dtype":"float64","order":"little"}]]}}},"view":{"type":"object","name":"CDSView","id":"p1377","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1378"}}},"glyph":{"type":"object","name":"Line","id":"p1373","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"#3f3f3f","line_width":2.2,"line_dash":[6]}},"nonselection_glyph":{"type":"object","name":"Line","id":"p1374","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"#3f3f3f","line_alpha":0.1,"line_width":2.2,"line_dash":[6]}},"muted_glyph":{"type":"object","name":"Line","id":"p1375","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"#3f3f3f","line_alpha":0.2,"line_width":2.2,"line_dash":[6]}}}}],"toolbar":{"type":"object","name":"Toolbar","id":"p1342","attributes":{"tools":[{"type":"object","name":"PanTool","id":"p1355"},{"type":"object","name":"WheelZoomTool","id":"p1356","attributes":{"renderers":"auto"}},{"type":"object","name":"ResetTool","id":"p1357"},{"type":"object","name":"SaveTool","id":"p1358"}]}},"left":[{"type":"object","name":"LinearAxis","id":"p1350","attributes":{"ticker":{"type":"object","name":"BasicTicker","id":"p1351","attributes":{"mantissas":[1,2,5]}},"formatter":{"type":"object","name":"BasicTickFormatter","id":"p1352"},"axis_label":"Cumulative fraction","major_label_policy":{"type":"object","name":"AllLabels","id":"p1353"}}}],"below":[{"type":"object","name":"LinearAxis","id":"p1345","attributes":{"ticker":{"type":"object","name":"BasicTicker","id":"p1346","attributes":{"mantissas":[1,2,5]}},"formatter":{"type":"object","name":"BasicTickFormatter","id":"p1347"},"axis_label":"KLD (bits)","major_label_policy":{"type":"object","name":"AllLabels","id":"p1348"}}}],"center":[{"type":"object","name":"Grid","id":"p1349","attributes":{"axis":{"id":"p1345"},"grid_line_alpha":0.3}},{"type":"object","name":"Grid","id":"p1354","attributes":{"dimension":1,"axis":{"id":"p1350"},"grid_line_alpha":0.3}},{"type":"object","name":"Legend","id":"p1368","attributes":{"location":"bottom_right","items":[{"type":"object","name":"LegendItem","id":"p1369","attributes":{"label":{"type":"value","value":"Ungauged best-donor minimum KLD"},"renderers":[{"id":"p1365"}]}},{"type":"object","name":"LegendItem","id":"p1379","attributes":{"label":{"type":"value","value":"Training station-pair KLD"},"renderers":[{"id":"p1376"}]}}]}}]}}]}}';
                  const render_items = [{"docid":"ea539a7a-db02-4e72-ae44-0497d0eb4085","roots":{"p1334":"cea58a3e-512e-47d0-9f09-166f695368e5"},"root_ids":["p1334"]}];
                  root.Bokeh.embed.embed_items(docs_json, render_items);
                  }
                  if (root.Bokeh !== undefined) {
                    embed_document(root);
                  } else {
                    let attempts = 0;
                    const timer = setInterval(function(root) {
                      if (root.Bokeh !== undefined) {
                        clearInterval(timer);
                        embed_document(root);
                      } else {
                        attempts++;
                        if (attempts > 100) {
                          clearInterval(timer);
                          console.log("Bokeh: ERROR: Unable to run BokehJS code because BokehJS library is missing");
                        }
                      }
                    }, 10, root)
                  }
                })(window);
              });
            };
            if (document.readyState != "loading") fn();
            else document.addEventListener("DOMContentLoaded", fn);
          })();
        },
    function(Bokeh) {
        }
      ];
    
      function run_inline_js() {
        for (let i = 0; i < inline_js.length; i++) {
          inline_js[i].call(root, root.Bokeh);
        }
      }
    
      if (root._bokeh_is_loading === 0) {
        console.debug("Bokeh: BokehJS loaded, going straight to plotting");
        run_inline_js();
      } else {
        load_libs(css_urls, js_urls, function() {
          console.debug("Bokeh: BokehJS plotting callback run at", now());
          run_inline_js();
        });
      }
    }(window));
  };
  if (document.readyState != "loading") fn();
  else document.addEventListener("DOMContentLoaded", fn);
})();