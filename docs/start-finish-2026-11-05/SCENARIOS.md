# Complete directed scenario catalogue

All lengths, directions, layers and task placements below belong to the inferred model, not surveyed official geometry. Segment IDs are zero-based. Strategies are analysis annotations; firmware does not receive segment IDs or coordinates.

| Segment / vertices | Phase | Model m | Turn deg | Situations | Response / limitation |
|---|---|---|---|---|---|
| 0 / 0->1 | Start and central approach | 0.0..0.125 | 0 | straight, start | centered PD with bounded PWM and acceleration; physical start crossing starts referee clock |
| 1 / 1->2 | Start and central approach | 0.125..0.485 | 0.0 | straight | centered PD with bounded PWM and acceleration |
| 2 / 2->3 | Start and central approach | 0.485..0.6764 | 19.86 | curve | continuous position PD; lower speed with increasing error |
| 3 / 3->4 | Start and central approach | 0.6764..0.8782 | 28.16 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 4 / 4->5 | Start and central approach | 0.8782..1.0322 | 28.85 | curve | continuous position PD; lower speed with increasing error |
| 5 / 5->6 | Start and central approach | 1.0322..1.4322 | 13.13 | curve | continuous position PD; lower speed with increasing error |
| 6 / 6->7 | Start and central approach | 1.4322..1.5938 | 21.8 | curve | continuous position PD; lower speed with increasing error |
| 7 / 7->8 | Start and central approach | 1.5938..1.774 | 34.51 | curve | continuous position PD; lower speed with increasing error |
| 8 / 8->9 | Start and central approach | 1.774..2.3344 | 31.64 | curve | continuous position PD; lower speed with increasing error |
| 9 / 9->10 | Start and central approach | 2.3344..2.5178 | -23.82 | curve | continuous position PD; lower speed with increasing error |
| 10 / 10->11 | Start and central approach | 2.5178..2.6989 | -36.15 | curve | continuous position PD; lower speed with increasing error |
| 11 / 11->12 | Start and central approach | 2.6989..3.6089 | -27.98 | curve | continuous position PD; lower speed with increasing error |
| 12 / 12->13 | Start and central approach | 3.6089..4.7389 | 0.0 | straight, overlap | centered PD with bounded PWM and acceleration; world resolves height; firmware must use observable context for any branch |
| 13 / 13->14 | Start and central approach | 4.7389..4.9274 | -21.8 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 14 / 14->15 | Start and central approach | 4.9274..5.0995 | -32.66 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 15 / 15->16 | Start and central approach | 5.0995..5.2595 | -35.54 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 16 / 16->17 | Start and central approach | 5.2595..5.4183 | -28.18 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 17 / 17->18 | Start and central approach | 5.4183..5.605 | -41.44 | curve | continuous position PD; lower speed with increasing error |
| 18 / 18->19 | Raised crossing 1 | 5.605..6.51 | -20.38 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 19 / 19->20 | Raised crossing 1 | 6.51..6.7155 | -18.43 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 20 / 20->21 | Raised crossing 1 | 6.7155..6.8958 | -37.87 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 21 / 21->22 | Raised crossing 1 | 6.8958..7.0208 | -33.69 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 22 / 22->23 | Raised crossing 1 | 7.0208..7.2137 | -31.22 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 23 / 23->24 | Raised crossing 1 | 7.2137..7.3358 | -23.79 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 24 / 24->25 | Raised crossing 1 | 7.3358..8.3108 | -34.99 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 25 / 25->26 | Raised crossing 1 | 8.3108..8.4993 | -21.8 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 26 / 26->27 | Raised crossing 1 | 8.4993..8.6713 | -32.66 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 27 / 27->28 | Raised crossing 1 | 8.6713..9.2413 | -35.54 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 28 / 28->29 | Raised crossing 1 | 9.2413..9.376 | -21.8 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 29 / 29->30 | Raised crossing 1 | 9.376..9.504 | -29.54 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 30 / 30->31 | Raised crossing 1 | 9.504..9.6338 | -23.02 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 31 / 31->32 | Raised crossing 1 | 9.6338..10.7138 | -15.64 | curve, grade_transition, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints; world resolves height; firmware must use observable context for any branch |
| 32 / 32->33 | Raised crossing 1 | 10.7138..11.5038 | 0.0 | straight, overlap | centered PD with bounded PWM and acceleration; world resolves height; firmware must use observable context for any branch |
| 33 / 33->34 | Central and left serpentine | 11.5038..11.645 | -22.93 | curve | continuous position PD; lower speed with increasing error |
| 34 / 34->35 | Central and left serpentine | 11.645..11.809 | -29.5 | curve | continuous position PD; lower speed with increasing error |
| 35 / 35->36 | Central and left serpentine | 11.809..11.9512 | -27.44 | curve | continuous position PD; lower speed with increasing error |
| 36 / 36->37 | Central and left serpentine | 11.9512..12.099 | -34.09 | curve | continuous position PD; lower speed with increasing error |
| 37 / 37->38 | Central and left serpentine | 12.099..12.271 | -30.5 | curve | continuous position PD; lower speed with increasing error |
| 38 / 38->39 | Central and left serpentine | 12.271..12.4163 | -31.59 | curve | continuous position PD; lower speed with increasing error |
| 39 / 39->40 | Central and left serpentine | 12.4163..12.564 | -32.25 | curve | continuous position PD; lower speed with increasing error |
| 40 / 40->41 | Central and left serpentine | 12.564..12.7166 | -30.09 | curve | continuous position PD; lower speed with increasing error |
| 41 / 41->42 | Central and left serpentine | 12.7166..13.7368 | -30.48 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 42 / 42->43 | Central and left serpentine | 13.7368..13.88 | 23.65 | curve | continuous position PD; lower speed with increasing error |
| 43 / 43->44 | Central and left serpentine | 13.88..14.0464 | 32.49 | curve | continuous position PD; lower speed with increasing error |
| 44 / 44->45 | Central and left serpentine | 14.0464..14.1818 | 28.5 | curve | continuous position PD; lower speed with increasing error |
| 45 / 45->46 | Central and left serpentine | 14.1818..14.3362 | 33.29 | curve | continuous position PD; lower speed with increasing error |
| 46 / 46->47 | Central and left serpentine | 14.3362..14.4854 | 21.39 | curve | continuous position PD; lower speed with increasing error |
| 47 / 47->48 | Central and left serpentine | 14.4854..14.6058 | 34.8 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 48 / 48->49 | Central and left serpentine | 14.6058..14.8071 | -21.8 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 49 / 49->50 | Central and left serpentine | 14.8071..14.9615 | -34.38 | curve | continuous position PD; lower speed with increasing error |
| 50 / 50->51 | Central and left serpentine | 14.9615..15.0866 | -26.76 | curve | continuous position PD; lower speed with increasing error |
| 51 / 51->52 | Central and left serpentine | 15.0866..15.2299 | -31.54 | curve | continuous position PD; lower speed with increasing error |
| 52 / 52->53 | Central and left serpentine | 15.2299..15.4048 | -29.79 | curve | continuous position PD; lower speed with increasing error |
| 53 / 53->54 | Central and left serpentine | 15.4048..15.9648 | -30.45 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 54 / 54->55 | Central and left serpentine | 15.9648..16.134 | 33.65 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 55 / 55->56 | Central and left serpentine | 16.134..16.3074 | 22.61 | curve | continuous position PD; lower speed with increasing error |
| 56 / 56->57 | Central and left serpentine | 16.3074..16.8424 | 33.23 | curve | continuous position PD; lower speed with increasing error |
| 57 / 57->58 | Central and left serpentine | 16.8424..17.0168 | 27.3 | curve | continuous position PD; lower speed with increasing error |
| 58 / 58->59 | Central and left serpentine | 17.0168..17.1892 | 33.16 | curve | continuous position PD; lower speed with increasing error |
| 59 / 59->60 | Central and left serpentine | 17.1892..17.7092 | 28.99 | curve | continuous position PD; lower speed with increasing error |
| 60 / 60->61 | Central and left serpentine | 17.7092..17.9174 | -23.55 | curve | continuous position PD; lower speed with increasing error |
| 61 / 61->62 | Central and left serpentine | 17.9174..18.0409 | -34.14 | curve | continuous position PD; lower speed with increasing error |
| 62 / 62->63 | Central and left serpentine | 18.0409..18.217 | -25.24 | curve | continuous position PD; lower speed with increasing error |
| 63 / 63->64 | Central and left serpentine | 18.217..18.3379 | 23.23 | curve | continuous position PD; lower speed with increasing error |
| 64 / 64->65 | Central and left serpentine | 18.3379..18.4809 | 23.79 | curve | continuous position PD; lower speed with increasing error |
| 65 / 65->66 | Central and left serpentine | 18.4809..18.6174 | 28.04 | curve | continuous position PD; lower speed with increasing error |
| 66 / 66->67 | Central and left serpentine | 18.6174..18.7614 | 28.75 | curve | continuous position PD; lower speed with increasing error |
| 67 / 67->68 | Central and left serpentine | 18.7614..18.8852 | 26.31 | curve | continuous position PD; lower speed with increasing error |
| 68 / 68->69 | Central and left serpentine | 18.8852..19.0006 | 25.71 | curve | continuous position PD; lower speed with increasing error |
| 69 / 69->70 | Central and left serpentine | 19.0006..19.131 | 22.05 | curve | continuous position PD; lower speed with increasing error |
| 70 / 70->71 | Central and left serpentine | 19.131..19.2863 | 28.78 | curve | continuous position PD; lower speed with increasing error |
| 71 / 71->72 | Central and left serpentine | 19.2863..19.4004 | 28.01 | curve | continuous position PD; lower speed with increasing error |
| 72 / 72->73 | Central and left serpentine | 19.4004..19.5815 | 22.47 | curve | continuous position PD; lower speed with increasing error |
| 73 / 73->74 | Central and left serpentine | 19.5815..19.7188 | -26.77 | curve | continuous position PD; lower speed with increasing error |
| 74 / 74->75 | Central and left serpentine | 19.7188..19.8933 | -29.59 | curve | continuous position PD; lower speed with increasing error |
| 75 / 75->76 | Raised crossing 2 | 19.8933..20.4133 | -27.3 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 76 / 76->77 | Raised crossing 2 | 20.4133..20.5748 | 21.8 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 77 / 77->78 | Raised crossing 2 | 20.5748..20.6703 | 25.32 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 78 / 78->79 | Raised crossing 2 | 20.6703..20.8174 | 25.06 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 79 / 79->80 | Raised crossing 2 | 20.8174..21.7724 | 17.82 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 80 / 80->81 | Raised crossing 2 | 21.7724..21.9289 | -26.57 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 81 / 81->82 | Raised crossing 2 | 21.9289..22.115 | -32.74 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 82 / 82->83 | Raised crossing 2 | 22.115..22.23 | -30.7 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 83 / 83->84 | Raised crossing 2 | 22.23..22.3508 | -24.44 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 84 / 84->85 | Raised crossing 2 | 22.3508..22.4676 | -22.29 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 85 / 85->86 | Raised crossing 2 | 22.4676..22.5688 | -23.04 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 86 / 86->87 | Raised crossing 2 | 22.5688..25.3338 | -20.22 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 87 / 87->88 | Raised crossing 2 | 25.3338..25.4066 | -15.95 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 88 / 88->89 | Raised crossing 2 | 25.4066..25.5347 | -22.71 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 89 / 89->90 | Raised crossing 2 | 25.5347..25.6221 | -20.38 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 90 / 90->91 | Raised crossing 2 | 25.6221..25.729 | -20.18 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 91 / 91->92 | Raised crossing 2 | 25.729..27.504 | -10.78 | curve, grade_transition, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints; world resolves height; firmware must use observable context for any branch |
| 92 / 92->93 | Raised crossing 2 | 27.504..27.6109 | -10.78 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 93 / 93->94 | Raised crossing 2 | 27.6109..27.7609 | -26.09 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 94 / 94->95 | Raised crossing 2 | 27.7609..27.9086 | -29.17 | curve | continuous position PD; lower speed with increasing error |
| 95 / 95->96 | Left circular approach | 27.9086..30.6486 | -23.96 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 96 / 96->97 | Left circular approach | 30.6486..30.7833 | -21.8 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 97 / 97->98 | Left circular approach | 30.7833..30.9071 | -24.84 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 98 / 98->99 | Left circular approach | 30.9071..31.0036 | -22.11 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 99 / 99->100 | Left circular approach | 31.0036..31.1136 | -21.25 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 100 / 100->101 | Left circular approach | 31.1136..31.239 | -23.5 | curve | continuous position PD; lower speed with increasing error |
| 101 / 101->102 | Left circular approach | 31.239..31.3309 | -21.5 | curve | continuous position PD; lower speed with increasing error |
| 102 / 102->103 | Left circular approach | 31.3309..31.4159 | -16.93 | curve | continuous position PD; lower speed with increasing error |
| 103 / 103->104 | Left circular approach | 31.4159..31.5468 | -21.49 | curve | continuous position PD; lower speed with increasing error |
| 104 / 104->105 | Left circular approach | 31.5468..31.6972 | -28.03 | curve | continuous position PD; lower speed with increasing error |
| 105 / 105->106 | Raised crossing 3 and seesaw | 31.6972..31.8503 | -30.18 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 106 / 106->107 | Raised crossing 3 and seesaw | 31.8503..32.0259 | -33.47 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 107 / 107->108 | Raised crossing 3 and seesaw | 32.0259..32.1692 | -34.15 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 108 / 108->109 | Raised crossing 3 and seesaw | 32.1692..32.2934 | -20.65 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 109 / 109->110 | Raised crossing 3 and seesaw | 32.2934..32.3954 | -28.79 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 110 / 110->111 | Raised crossing 3 and seesaw | 32.3954..32.4554 | -11.31 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 111 / 111->112 | Raised crossing 3 and seesaw | 32.4554..32.59 | -21.8 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 112 / 112->113 | Raised crossing 3 and seesaw | 32.59..32.7138 | -24.84 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 113 / 113->114 | Raised crossing 3 and seesaw | 32.7138..32.8104 | -22.11 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 114 / 114->115 | Raised crossing 3 and seesaw | 32.8104..33.1005 | -19.28 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 115 / 115->116 | Raised crossing 3 and seesaw | 33.1005..34.4005 | -2.2 | straight, raised_occurrence, seesaw | centered PD with bounded PWM and acceleration; PD through load change; no measured rollback/tipping feedback |
| 116 / 116->117 | Raised crossing 3 and seesaw | 34.4005..34.8706 | 1.44 | straight, raised_occurrence | centered PD with bounded PWM and acceleration |
| 117 / 117->118 | Raised crossing 3 and seesaw | 34.8706..36.0406 | -1.22 | straight, grade_transition, raised_occurrence | centered PD with bounded PWM and acceleration; same observed-line control; traction/height remain physical constraints |
| 118 / 118->119 | Raised crossing 3 and seesaw | 36.0406..36.5107 | -0.61 | straight | centered PD with bounded PWM and acceleration |
| 119 / 119->120 | Upper-right loops | 36.5107..36.9008 | -0.86 | straight | centered PD with bounded PWM and acceleration |
| 120 / 120->121 | Upper-right loops | 36.9008..37.0262 | -22.03 | curve | continuous position PD; lower speed with increasing error |
| 121 / 121->122 | Upper-right loops | 37.0262..37.1005 | -18.78 | curve | continuous position PD; lower speed with increasing error |
| 122 / 122->123 | Upper-right loops | 37.1005..37.2191 | -20.08 | curve | continuous position PD; lower speed with increasing error |
| 123 / 123->124 | Upper-right loops | 37.2191..37.4945 | -24.52 | curve | continuous position PD; lower speed with increasing error |
| 124 / 124->125 | Upper-right loops | 37.4945..38.2045 | -3.12 | straight | centered PD with bounded PWM and acceleration |
| 125 / 125->126 | Upper-right loops | 38.2045..38.4148 | -28.39 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 126 / 126->127 | Upper-right loops | 38.4148..38.5328 | -25.22 | curve | continuous position PD; lower speed with increasing error |
| 127 / 127->128 | Upper-right loops | 38.5328..38.6587 | -29.54 | curve | continuous position PD; lower speed with increasing error |
| 128 / 128->129 | Upper-right loops | 38.6587..38.7852 | -25.28 | curve | continuous position PD; lower speed with increasing error |
| 129 / 129->130 | Upper-right loops | 38.7852..38.8912 | -26.57 | curve | continuous position PD; lower speed with increasing error |
| 130 / 130->131 | Upper-right loops | 38.8912..39.0613 | -20.7 | curve | continuous position PD; lower speed with increasing error |
| 131 / 131->132 | Upper-right loops | 39.0613..39.7713 | -24.3 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 132 / 132->133 | Upper-right loops | 39.7713..40.0463 | 1.04 | straight | centered PD with bounded PWM and acceleration |
| 133 / 133->134 | Upper-right loops | 40.0463..40.1515 | 24.3 | curve | continuous position PD; lower speed with increasing error |
| 134 / 134->135 | Upper-right loops | 40.1515..40.2648 | 23.23 | curve | continuous position PD; lower speed with increasing error |
| 135 / 135->136 | Upper-right loops | 40.2648..40.3614 | 20.17 | curve | continuous position PD; lower speed with increasing error |
| 136 / 136->137 | Upper-right loops | 40.3614..40.4764 | 21.25 | curve | continuous position PD; lower speed with increasing error |
| 137 / 137->138 | Upper-right loops | 40.4764..40.573 | 21.25 | curve | continuous position PD; lower speed with increasing error |
| 138 / 138->139 | Upper-right loops | 40.573..40.6897 | 22.01 | curve | continuous position PD; lower speed with increasing error |
| 139 / 139->140 | Upper-right loops | 40.6897..40.8606 | 26.18 | curve | continuous position PD; lower speed with increasing error |
| 140 / 140->141 | Upper-right loops | 40.8606..41.7656 | 20.56 | curve | continuous position PD; lower speed with increasing error |
| 141 / 141->142 | Upper-right loops | 41.7656..41.9126 | 17.82 | curve | continuous position PD; lower speed with increasing error |
| 142 / 142->143 | Raised crossing 4 and lift | 41.9126..42.054 | 27.18 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 143 / 143->144 | Raised crossing 4 and lift | 42.054..42.2335 | 32.12 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 144 / 144->145 | Raised crossing 4 and lift | 42.2335..42.3711 | 31.97 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 145 / 145->146 | Raised crossing 4 and lift | 42.3711..42.4808 | 24.06 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 146 / 146->147 | Raised crossing 4 and lift | 42.4808..42.5747 | 21.65 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 147 / 147->148 | Raised crossing 4 and lift | 42.5747..43.1047 | 24.66 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 148 / 148->149 | Raised crossing 4 and lift | 43.1047..43.2566 | -16.7 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 149 / 149->150 | Raised crossing 4 and lift | 43.2566..43.4157 | -29.03 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 150 / 150->151 | Raised crossing 4 and lift | 43.4157..43.5106 | -25.29 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 151 / 151->152 | Raised crossing 4 and lift | 43.5106..43.6514 | -24.55 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 152 / 152->153 | Raised crossing 4 and lift | 43.6514..43.8054 | -29.64 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 153 / 153->154 | Raised crossing 4 and lift | 43.8054..43.9598 | -29.34 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 154 / 154->155 | Raised crossing 4 and lift | 43.9598..45.8048 | -24.9 | curve, grade_transition, raised_occurrence, overlap, lift | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints; world resolves height; firmware must use observable context for any branch; bound observed prefix; stop31s; narrow exit100ms within1500ms |
| 155 / 155->156 | Raised crossing 4 and lift | 45.8048..45.925 | -16.93 | curve, raised_occurrence, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 156 / 156->157 | Raised crossing 4 and lift | 45.925..46.0948 | -30.46 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 157 / 157->158 | Raised crossing 4 and lift | 46.0948..46.2716 | -34.48 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 158 / 158->159 | Raised crossing 4 and lift | 46.2716..46.4528 | -36.11 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 159 / 159->160 | Raised crossing 4 and lift | 46.4528..46.5831 | -29.55 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 160 / 160->161 | Raised crossing 4 and lift | 46.5831..46.644 | -23.01 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 161 / 161->162 | Raised crossing 4 and lift | 46.644..46.7644 | -14.23 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 162 / 162->163 | Raised crossing 4 and lift | 46.7644..46.8948 | -27.71 | curve, raised_occurrence | continuous position PD; lower speed with increasing error |
| 163 / 163->164 | Raised crossing 4 and lift | 46.8948..47.0018 | -20.12 | curve, grade_transition, raised_occurrence | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 164 / 164->165 | Raised crossing 4 and lift | 47.0018..47.1489 | -27.62 | curve | continuous position PD; lower speed with increasing error |
| 165 / 165->166 | Post-lift return | 47.1489..47.252 | -23.82 | curve | continuous position PD; lower speed with increasing error |
| 166 / 166->167 | Post-lift return | 47.252..47.341 | -24.12 | curve | continuous position PD; lower speed with increasing error |
| 167 / 167->168 | Post-lift return | 47.341..47.4868 | -29.68 | curve | continuous position PD; lower speed with increasing error |
| 168 / 168->169 | Post-lift return | 47.4868..47.5992 | -1.31 | straight, overlap | centered PD with bounded PWM and acceleration; world resolves height; firmware must use observable context for any branch |
| 169 / 169->170 | Post-lift return | 47.5992..47.8192 | -19.55 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 170 / 170->171 | Post-lift return | 47.8192..48.0493 | -2.55 | straight | centered PD with bounded PWM and acceleration |
| 171 / 171->172 | Post-lift return | 48.0493..48.1379 | -15.14 | curve | continuous position PD; lower speed with increasing error |
| 172 / 172->173 | Post-lift return | 48.1379..48.273 | -22.6 | curve | continuous position PD; lower speed with increasing error |
| 173 / 173->174 | Post-lift return | 48.273..48.3691 | -23.11 | curve | continuous position PD; lower speed with increasing error |
| 174 / 174->175 | Post-lift return | 48.3691..49.7792 | -27.29 | curve | continuous position PD; lower speed with increasing error |
| 175 / 175->176 | Post-lift return | 49.7792..50.4192 | -0.16 | straight | centered PD with bounded PWM and acceleration |
| 176 / 176->177 | Post-lift return | 50.4192..51.5642 | -0.7 | straight, overlap | centered PD with bounded PWM and acceleration; world resolves height; firmware must use observable context for any branch |
| 177 / 177->178 | Post-lift return | 51.5642..51.6662 | -11.06 | curve, overlap | continuous position PD; lower speed with increasing error; world resolves height; firmware must use observable context for any branch |
| 178 / 178->179 | Post-lift return | 51.6662..51.7873 | -26.98 | curve | continuous position PD; lower speed with increasing error |
| 179 / 179->180 | Post-lift return | 51.7873..51.8687 | -9.2 | straight | centered PD with bounded PWM and acceleration |
| 180 / 180->181 | Post-lift return | 51.8687..51.9937 | -26.25 | curve | continuous position PD; lower speed with increasing error |
| 181 / 181->182 | Post-lift return | 51.9937..52.5337 | -15.73 | curve | continuous position PD; lower speed with increasing error |
| 182 / 182->183 | Post-lift return | 52.5337..52.6343 | 26.03 | curve | continuous position PD; lower speed with increasing error |
| 183 / 183->184 | Post-lift return | 52.6343..52.7764 | 24.15 | curve | continuous position PD; lower speed with increasing error |
| 184 / 184->185 | Post-lift return | 52.7764..52.8795 | 25.25 | curve | continuous position PD; lower speed with increasing error |
| 185 / 185->186 | Post-lift return | 52.8795..52.985 | 19.48 | curve | continuous position PD; lower speed with increasing error |
| 186 / 186->187 | Post-lift return | 52.985..53.1103 | 23.17 | curve | continuous position PD; lower speed with increasing error |
| 187 / 187->188 | Post-lift return | 53.1103..53.2283 | 25.01 | curve | continuous position PD; lower speed with increasing error |
| 188 / 188->189 | Post-lift return | 53.2283..53.3471 | 21.76 | curve | continuous position PD; lower speed with increasing error |
| 189 / 189->190 | Post-lift return | 53.3471..53.9821 | 14.62 | curve, grade_transition | continuous position PD; lower speed with increasing error; same observed-line control; traction/height remain physical constraints |
| 190 / 190->191 | Post-lift return | 53.9821..54.1822 | 1.43 | straight, grade_transition, overlap | centered PD with bounded PWM and acceleration; same observed-line control; traction/height remain physical constraints; world resolves height; firmware must use observable context for any branch |
| 191 / 191->192 | TAIWAN sharp turns and finish | 54.1822..54.4572 | -1.43 | straight, extra_paint | centered PD with bounded PWM and acceleration; bounded ambiguity; broad/split alone cannot identify mission |
| 192 / 192->193 | TAIWAN sharp turns and finish | 54.4572..55.3422 | 0.0 | straight, extra_paint | centered PD with bounded PWM and acceleration; bounded ambiguity; broad/split alone cannot identify mission |
| 193 / 193->194 | TAIWAN sharp turns and finish | 55.3422..55.6972 | 90.0 | sharp_turn | reduce translation before bounded turn and confirmed return |
| 194 / 194->195 | TAIWAN sharp turns and finish | 55.6972..56.6175 | 70.97 | sharp_turn | reduce translation before bounded turn and confirmed return |
| 195 / 195->196 | TAIWAN sharp turns and finish | 56.6175..57.533 | -142.84 | acute_V | slow approach; ordered chosen-side capture; no early opposite-branch exit |
| 196 / 196->197 | TAIWAN sharp turns and finish | 57.533..57.898 | 71.86 | sharp_turn, extra_paint | reduce translation before bounded turn and confirmed return; bounded ambiguity; broad/split alone cannot identify mission |
| 197 / 197->198 | TAIWAN sharp turns and finish | 57.898..58.783 | 90.0 | sharp_turn, extra_paint | reduce translation before bounded turn and confirmed return; bounded ambiguity; broad/split alone cannot identify mission |
| 198 / 198->199 | TAIWAN sharp turns and finish | 58.783..59.133 | -90.0 | sharp_turn, extra_paint, contextual_right | reduce translation before bounded turn and confirmed return; bounded ambiguity; broad/split alone cannot identify mission; bound post-lift R L W L R L R L W selects R at terminal W only |
| 199 / 199->200 | TAIWAN sharp turns and finish | 59.133..60.0461 | -75.74 | sharp_turn | reduce translation before bounded turn and confirmed return |
| 200 / 200->201 | TAIWAN sharp turns and finish | 60.0461..60.9618 | 150.86 | acute_V | slow approach; ordered chosen-side capture; no early opposite-branch exit |
| 201 / 201->202 | TAIWAN sharp turns and finish | 60.9618..61.8737 | -151.17 | acute_V | slow approach; ordered chosen-side capture; no early opposite-branch exit |
| 202 / 202->203 | TAIWAN sharp turns and finish | 61.8737..62.7934 | 150.27 | acute_V | slow approach; ordered chosen-side capture; no early opposite-branch exit |
| 203 / 203->204 | TAIWAN sharp turns and finish | 62.7934..63.0934 | -74.23 | sharp_turn | reduce translation before bounded turn and confirmed return |
| 204 / 204->205 | TAIWAN sharp turns and finish | 63.0934..64.0262 | -71.57 | sharp_turn | reduce translation before bounded turn and confirmed return |
| 205 / 205->206 | TAIWAN sharp turns and finish | 64.0262..64.2562 | 71.57 | sharp_turn | reduce translation before bounded turn and confirmed return |
| 206 / 206->207 | TAIWAN sharp turns and finish | 64.2562..65.1412 | 90.0 | sharp_turn | reduce translation before bounded turn and confirmed return |
| 207 / 207->208 | TAIWAN sharp turns and finish | 65.1412..66.2021 | -146.53 | acute_V | slow approach; ordered chosen-side capture; no early opposite-branch exit |
| 208 / 208->209 | TAIWAN sharp turns and finish | 66.2021..67.0521 | 146.53 | acute_V | slow approach; ordered chosen-side capture; no early opposite-branch exit |
| 209 / 209->210 | TAIWAN sharp turns and finish | 67.0521..67.1871 | 0.0 | straight, finish | centered PD with bounded PWM and acceleration; physical referee finish crossing; reference has no onboard finish stop |

## Unmodelled / unresolved
- arbitrary competition lettering
- explicit dashed/gap intervals (not encoded in this route)
- on-site mechanism placement variants
- complete rigid-body/tipping/contact
- measured tire slip/torque
- actual shortcut action (disabled; full A apex followed)
- verified F meaning and official exits
- onboard physical finish crossing detection
- central_x471
- central_x585
- left_circle_x117
- right_x1029
- central_y692
- bottom_y781
- F_task_undefined
- T_V_exit_direction
- on_site_seesaw_placement
- lift_occurrence_and_connections
- ground_backing_height_extent_material_unmeasured
