from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive


# Initialize RPA instances
page = browser.page()
http = HTTP()
table = Tables()
pdf = PDF()
lib = Archive()

# URLs and File Directories
robot_order_site = "https://robotsparebinindustries.com/#/robot-order"
data_download_url = "https://robotsparebinindustries.com/orders.csv"
filename = "orders.csv"
download_dir = "output/downloads"
file_path = download_dir + "/" + filename


@task
def order_robots_from_RobotSparePartBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    # Workflow
    open_robot_order_website()

    orders = get_orders()

    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        pdf_file = store_receipt_as_pdf(order)
        screenshot = screenshot_robot(order)
        embed_screenshot_to_receipt(screenshot, pdf_file)
        order_another_robot()

    archive_receipts()


def open_robot_order_website():
    """
    Navigate to robot order webpage
    """
    browser.goto(robot_order_site)


def close_annoying_modal():
    """Close annoying pop-up modal on first page"""
    page.get_by_role("button", name="OK").click()


def get_orders():
    """Download the orders file, read it as a table, and return the result"""
    http.download(
        url=data_download_url,
        target_file=file_path,
        overwrite=True,
    )

    data = table.read_table_from_csv(file_path, header=True)
    return data


def fill_the_form(order):
    """Fill form, preview the robot being ordered and order"""

    # fill form
    page.get_by_label("Head").select_option(order["Head"])
    page.locator(f'id=id-body-{order["Body"]}').click()
    page.get_by_placeholder("Enter the part number for the legs").fill(order["Legs"])
    page.locator("id=address").fill(order["Address"])

    # preview and order robot
    page.locator("id=preview").click()
    page.locator("id=order").click()

    # check for errors
    handle_errors()


def handle_errors():
    """
    Sometimes the submit order form fails when clicking on order.
    This error can be removed by clicking the order button again. However, sometimes one click doesn't work.
    This function continues to check for the error until it's resolved.
    """
    while True:  # keep checking until the error message disappears
        error = page.query_selector(".alert.alert-danger")
        if error:
            page.locator("id=order").click()
        else:
            break  # exit the loop if the error message is not present


def order_another_robot():
    """Place another robot order"""
    page.locator("id=order-another").click()


def store_receipt_as_pdf(order_number):
    """Store each order HTML receipt as a PDF and title pdf filename by order number"""
    pdf_file_path = (
        f'output/receipts/Robot_receipt_order_number_{order_number["Order number"]}.pdf'
    )
    receipt_html = page.locator("id=receipt").inner_html()
    pdf.html_to_pdf(
        receipt_html,
        pdf_file_path,
    )
    return pdf_file_path


def screenshot_robot(order_number):
    """Store a screenshot of the ordered robot and title file by order number"""

    screenshot_path = f'output/screenshots/Robot_screenshot_order_number{order_number["Order number"]}.png'
    page.locator("id=robot-preview-image").screenshot(path=screenshot_path)
    return screenshot_path


def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Embed screenshot image of each robot ordered to receipt PDF"""
    pdf.add_files_to_pdf([screenshot], target_document=pdf_file, append=True)


def archive_receipts():
    """Archive receipts as a zip file"""
    lib.archive_folder_with_zip("output/receipts", "output/robot_order_receipts.zip")
