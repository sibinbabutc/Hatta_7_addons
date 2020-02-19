<html>
<head>
    <style type="text/css">
        table.heading {
            border-collapse: collapse;
            width: 100%;
            page-break-inside: auto
        }
        table.heading td, th {
            page-break-inside: auto
        }
        table.heading thead {
            display: table-header-group
        }
        table.heading tfoot {
            display: table-row-group
        }
        table.heading tr {
            page-break-inside: avoid
        }
        ${css}
    </style>
    <header></header>
</head>
<body>
    %for crm in objects :
    <% setLang(crm.partner_id.lang) %>
    <table width="100%">
        <tr width="100%">
            <td align="center"><strong style="font-size: 20px;">Remarks</strong></td>
        </tr>
    </table>
    <table width="100%">
        <tr width="100%">
            <td width="20%"><strong style="font-size: 14px;">Your RFQ Number</strong></td>
            <td width="80%"><strong style="font-size: 14px;">${crm.customer_rfq}</strong></td>
        </tr>
        <tr width="100%">
            <td width="20%"><strong style="font-size: 14px;">Our Reference</strong></td>
            <td width="80%"><strong style="font-size: 14px;">${crm.reference}</strong></td>
        </tr>
    </table>
    %if get_remarks(crm)['line']:
    <table class="heading">
        <thead width="100%">
            <td style="border-top:1px solid black;border-left:1px solid black"></td>
            <td style="border-top:1px solid black;border-right:1px solid black"></td>
        </thead>
        <tr>
            <td width="10%" style="border-left:1px solid black;border-right:1px solid black;"><strong style="font-size: 14px;">SI No.</strong></td>
            <td width="900%" style="border-right:1px solid black;"><strong style="font-size: 14px;">Description</strong></td>
        <tr>
        %for rem_line in get_remarks(crm)['line']:
        <tr width="100%" style="page-break-inside: avoid">
            <td align="center" style="font-size: 12px;border: 1px solid black;">${rem_line.get('sequence', '')}</td>
            <td style="font-size: 12px;padding:0.3cm;page-break-inside: avoid;border: 1px solid black;">${rem_line.get('remark', '')}</td>
        </tr>
        %endfor
    </table>
    %endif
    <table width="100%">
        <tr width="100%">
            <td>${get_remarks(crm)['general_remark']}</td>
        </tr>
    </table>
    <table width="100%">
        %for img_line in get_remarks(crm)['image']:
        <tr width="100%">
            <td width="100%"><strong style="font-size: 14px;">${img_line.get('sequence', '')} : ${img_line.get('product_name', '')}</strong></td>
        </tr>
        <tr width="100%">
        <td width="100%" align="center"><img align="middle" src="data:image/png;base64,[${img_line.get('image','')}]" /></td>
        </tr>
        %endfor
    </table>
    <p style="page-break-after:always"></p>
    %endfor
</body>
</html>