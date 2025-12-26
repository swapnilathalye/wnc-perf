import java.io.*;
import java.math.BigDecimal;
import java.util.*;
import java.util.zip.GZIPInputStream;
import java.util.logging.*;

public class ConvertPerfToCsv {

    // Type codes
    static final byte NULL_TYPE = 0;
    static final byte BYTE_TYPE = 1;
    static final byte SHORT_TYPE = 2;
    static final byte INTEGER_TYPE = 3;
    static final byte LONG_TYPE = 4;
    static final byte FLOAT_TYPE = 5;
    static final byte DOUBLE_TYPE = 6;
    static final byte BOOLEAN_TYPE = 7;
    static final byte TIMESTAMP_AS_LONG_TYPE = 8;
    static final byte BIG_DECIMAL_TYPE = 9;
    static final byte OBJECT_TYPE = 10;

    private static final Logger logger = Logger.getLogger(ConvertPerfToCsv.class.getName());

    static {
        try {
            File baseDir = new File(System.getProperty("user.dir")).getParentFile();
            String logsDir = baseDir + File.separator + "backend" + File.separator + "logs";
            File logDir = new File(logsDir);
            if (!logDir.exists()) logDir.mkdirs();

            FileHandler fh = new FileHandler(new File(logDir, "converter.log").getAbsolutePath(), true);
            fh.setEncoding("UTF-8");
            fh.setFormatter(new SimpleFormatter());
            logger.addHandler(fh);
            logger.setLevel(Level.INFO);

            ConsoleHandler ch = new ConsoleHandler();
            ch.setLevel(Level.INFO);
            logger.addHandler(ch);

        } catch (IOException e) {
            System.err.println("Failed to initialize logger: " + e.getMessage());
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            logger.severe("Usage: java ConvertPerfToCsv <input.gz> <outputDir>");
            System.exit(1);
        }
        File input = new File(args[0]);
        File outDir = new File(args[1]);
        outDir.mkdirs();
        logger.info("Starting conversion for " + input.getAbsolutePath());
        convertAllMembers(input, outDir);
        logger.info("✅ Conversion finished");
    }

    static void convertAllMembers(File inputGz, File outDir) throws Exception {
        List<Map<String,Object>> summary = new ArrayList<>();

        try (FileInputStream fis = new FileInputStream(inputGz);
             GZIPInputStream gis = new GZIPInputStream(fis, 8192);
             ObjectInputStream ois = new ObjectInputStream(gis)) {

            // Version info
            int[] version = new int[4];
            for (int i = 0; i < 4; i++) version[i] = ois.readInt();
            String qualifier = (String) ois.readObject();
            logger.info("Version: " + Arrays.toString(version) + " " + qualifier);

            // Multiple tables
            while (true) {
                String tableName;
                try {
                    tableName = (String) ois.readObject();
                } catch (EOFException eof) {
                    logger.info("Reached EOF, no more tables");
                    break;
                }
                if (tableName == null) {
                    logger.info("Null table name, stopping");
                    break;
                }

                int nColumns = ois.readInt();
                String[] columnNames = new String[nColumns];
                for (int i = 0; i < nColumns; i++) {
                    columnNames[i] = (String) ois.readObject();
                }

                File csv = new File(outDir, tableName + ".csv");
                int rowCount = 0;
                try (PrintWriter pw = new PrintWriter(new OutputStreamWriter(new FileOutputStream(csv), "UTF-8"))) {
                    List<String> header = new ArrayList<>(Arrays.asList(columnNames));
                    header.add("latestSample");
                    pw.println(String.join(",", header));

                    while (ois.readBoolean()) {
                        List<String> vals = new ArrayList<>();
                        for (String col : columnNames) {
                            byte type = ois.readByte();
                            Object val = readValue(ois, type);
                            vals.add(val == null ? "" : escape(val.toString()));
                        }
                        vals.add("0"); // latestSample
                        pw.println(String.join(",", vals));
                        rowCount++;
                    }
                }
                logger.info("Processed table: " + tableName + " → " + rowCount + " rows, CSV: " + csv.getAbsolutePath());

                Map<String,Object> tableSummary = new LinkedHashMap<>();
                tableSummary.put("tableName", tableName);
                tableSummary.put("rows", rowCount);
                summary.add(tableSummary);
            }
        }

        // Write summary JSON
        File summaryFile = new File(outDir, "conversion_summary.json");
        try (PrintWriter pw = new PrintWriter(new OutputStreamWriter(new FileOutputStream(summaryFile), "UTF-8"))) {
            pw.println("[");
            for (int i = 0; i < summary.size(); i++) {
                Map<String,Object> ts = summary.get(i);
                pw.println("  {\"tableName\":\"" + ts.get("tableName") + "\", \"rows\":" + ts.get("rows") + "}" + (i < summary.size()-1 ? "," : ""));
            }
            pw.println("]");
        }
        logger.info("Wrote summary: " + summaryFile.getAbsolutePath());
    }

    static Object readValue(ObjectInputStream ois, byte type) throws Exception {
        switch (type) {
            case NULL_TYPE: return null;
            case BYTE_TYPE: return ois.readByte();
            case SHORT_TYPE: return ois.readShort();
            case INTEGER_TYPE: return ois.readInt();
            case LONG_TYPE: return ois.readLong();
            case FLOAT_TYPE: return ois.readFloat();
            case DOUBLE_TYPE: return ois.readDouble();
            case BOOLEAN_TYPE: return ois.readBoolean();
            case TIMESTAMP_AS_LONG_TYPE: return ois.readLong();
            case BIG_DECIMAL_TYPE: return (BigDecimal) ois.readObject();
            case OBJECT_TYPE: {
                Object o = ois.readObject();
                return (o == null) ? null : o.toString();
            }
            default:
                Object o = ois.readObject();
                return (o == null) ? null : o.toString();
        }
    }

    static String escape(String s) {
        boolean needQuote = s.contains(",") || s.contains("\"") || s.contains("\n");
        if (s.contains("\"")) s = s.replace("\"", "\"\"");
        return needQuote ? "\"" + s + "\"" : s;
    }
}
